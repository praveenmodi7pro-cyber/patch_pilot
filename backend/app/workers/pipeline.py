import asyncio
import os
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.events import event_broadcaster
from app.models.entities import (
    Project,
    Analysis,
    Bug,
    Repair,
    TestExecution,
    VerificationReport,
    RepositoryFile,
)
from app.services.activity import log_activity
from app.analysis.ingestion import RepositoryAnalyzer, compute_checksum
from app.analysis.ast_scanner import ASTCodeScanner
from app.analysis.ruff_scanner import RuffScanner
from app.ai.factory import get_ai_provider
from app.ai.base import DiagnosisFinding
from app.repair.patch_validator import PatchValidator
from app.repair.patch_applier import PatchApplier
from app.testing.test_runner import TestRunnerService, RegressionComparator, ParsedTestResults
from app.verification.decision_engine import VerificationDecisionEngine
from app.verification.report_generator import VerificationReportGenerator


class AnalysisPipelineRunner:
    """Executes the full 8-stage autonomous debugging and verification pipeline."""

    @classmethod
    async def run_pipeline(cls, analysis_id: str, db_session: Optional[AsyncSession] = None):
        try:
            if db_session is not None:
                await cls._run_pipeline_with_session(analysis_id, db_session)
            else:
                async with AsyncSessionLocal() as db:
                    await cls._run_pipeline_with_session(analysis_id, db)
        except Exception:
            import traceback
            traceback.print_exc()
            raise

    @classmethod
    async def _run_pipeline_with_session(cls, analysis_id: str, db: AsyncSession):
        # 1. Fetch analysis and project
        stmt = select(Analysis).where(Analysis.id == analysis_id)
        res = await db.execute(stmt)
        analysis = res.scalar_one_or_none()
        if not analysis:
            return

        proj_stmt = select(Project).where(Project.id == analysis.project_id)
        p_res = await db.execute(proj_stmt)
        project = p_res.scalar_one_or_none()
        if not project:
            analysis.status = "FAILED"
            analysis.error_message = "Project not found"
            await db.commit()
            return

        user_id = project.user_id
        project_id = project.id
        repo_storage_dir = settings.get_storage_path() / project_id

        if not repo_storage_dir.exists():
            analysis.status = "FAILED"
            analysis.error_message = "Repository source directory not found"
            await db.commit()
            await event_broadcaster.broadcast(analysis_id, "FAILED", {"error": analysis.error_message})
            return

        try:
            analysis.status = "INITIALIZING"
            analysis.started_at = datetime.now(timezone.utc)
            analysis.current_stage = "REPOSITORY_SCANNING"
            await db.commit()
            await event_broadcaster.broadcast(analysis_id, "STAGE_CHANGED", {"stage": "REPOSITORY_SCANNING"})

            # ==========================================
            # STAGE 1: REPOSITORY SCANNING
            # ==========================================
            analyzer = RepositoryAnalyzer(repo_storage_dir)
            repo_meta = analyzer.scan()

            # Verify supported language
            if repo_meta["primary_language"] != "python" and not any(f["path"].endswith(".py") for f in repo_meta["files"]):
                analysis.status = "FAILED"
                analysis.error_message = f"Language '{repo_meta['primary_language']}' is currently not supported for automated repair. Only Python is supported."
                await db.commit()
                await event_broadcaster.broadcast(analysis_id, "FAILED", {"error": analysis.error_message})
                return

            # Update or store files
            for f_info in repo_meta["files"]:
                file_stmt = select(RepositoryFile).where(
                    RepositoryFile.project_id == project_id,
                    RepositoryFile.path == f_info["path"]
                )
                f_res = await db.execute(file_stmt)
                existing_file = f_res.scalar_one_or_none()
                if not existing_file:
                    db.add(RepositoryFile(
                        project_id=project_id,
                        path=f_info["path"],
                        language=f_info["language"],
                        size=f_info["size"],
                        checksum=f_info["checksum"]
                    ))
            await db.commit()

            # ==========================================
            # STAGE 2: STATIC CODE ANALYSIS
            # ==========================================
            analysis.current_stage = "STATIC_CODE_ANALYSIS"
            await db.commit()
            await event_broadcaster.broadcast(analysis_id, "STAGE_CHANGED", {"stage": "STATIC_CODE_ANALYSIS"})

            ast_findings = ASTCodeScanner.scan_directory(repo_storage_dir)
            ruff_findings = RuffScanner.scan_directory(repo_storage_dir)
            static_findings = ast_findings + ruff_findings

            # ==========================================
            # STAGE 3: BASELINE TESTING & BUG DETECTION
            # ==========================================
            analysis.current_stage = "BUG_DETECTION"
            await db.commit()
            await event_broadcaster.broadcast(analysis_id, "STAGE_CHANGED", {"stage": "BUG_DETECTION"})

            has_tests = len(repo_meta["test_files"]) > 0
            baseline_test_results: Optional[ParsedTestResults] = None
            test_failures: List[Dict[str, Any]] = []

            if has_tests:
                baseline_test_results = TestRunnerService.execute_pytest(
                    repo_storage_dir,
                    timeout=settings.SANDBOX_TIMEOUT_SECONDS
                )
                test_failures = baseline_test_results.failures

            # Read source files sample for AI context
            source_samples = {}
            for f in repo_meta["files"]:
                if f["path"].endswith(".py") and not "test" in f["path"].lower():
                    try:
                        with open(repo_storage_dir / f["path"], "r", encoding="utf-8", errors="replace") as sf:
                            source_samples[f["path"]] = sf.read()[:3000]
                    except Exception:
                        pass

            repo_context = {
                "primary_language": repo_meta["primary_language"],
                "manifest_files": repo_meta["manifest_files"],
                "test_files": repo_meta["test_files"],
                "source_samples": source_samples,
            }

            # AI Provider Root Cause Analysis
            ai = get_ai_provider()
            diagnosis_result = await ai.analyze_root_cause(
                repository_context=repo_context,
                static_findings=static_findings,
                test_failures=test_failures,
            )

            stored_bugs: List[Bug] = []
            for finding in diagnosis_result.findings:
                bug = Bug(
                    analysis_id=analysis_id,
                    title=finding.title,
                    category=finding.category,
                    severity=finding.severity,
                    file_path=finding.file_path,
                    line_number=finding.line_number,
                    description=finding.root_cause,
                    root_cause=finding.root_cause,
                    evidence=finding.evidence,
                    confidence=finding.confidence,
                    status="detected"
                )
                db.add(bug)
                stored_bugs.append(bug)

            await db.commit()
            for b in stored_bugs:
                await db.refresh(b)
                await event_broadcaster.broadcast(analysis_id, "BUG_DETECTED", {
                    "id": b.id,
                    "title": b.title,
                    "severity": b.severity,
                    "file_path": b.file_path,
                })

            # If no bugs found
            if not stored_bugs:
                analysis.status = "COMPLETED"
                analysis.current_stage = "COMPLETED"
                analysis.completed_at = datetime.now(timezone.utc)
                await db.commit()
                await event_broadcaster.broadcast(analysis_id, "COMPLETED", {"message": "No bugs detected."})
                return

            # ==========================================
            # STAGE 4: PATCH GENERATION
            # ==========================================
            analysis.current_stage = "PATCH_GENERATION"
            await db.commit()
            await event_broadcaster.broadcast(analysis_id, "STAGE_CHANGED", {"stage": "PATCH_GENERATION"})

            # Generate patch for highest severity bug
            target_bug = stored_bugs[0]
            target_file_path = repo_storage_dir / target_bug.file_path
            file_content = ""
            if target_file_path.exists():
                with open(target_file_path, "r", encoding="utf-8", errors="replace") as f:
                    file_content = f.read()

            patch_result = await ai.generate_patch(
                bug_finding=DiagnosisFinding(
                    title=target_bug.title,
                    category=target_bug.category,
                    severity=target_bug.severity,
                    file_path=target_bug.file_path,
                    line_number=target_bug.line_number,
                    root_cause=target_bug.root_cause or target_bug.description,
                    evidence=target_bug.evidence or [],
                    suggested_fix="Fix the error while preserving existing structure",
                    confidence=target_bug.confidence,
                ),
                file_contents={target_bug.file_path: file_content}
            )

            repair = Repair(
                bug_id=target_bug.id,
                analysis_id=analysis_id,
                status="generated",
                patch_content=patch_result.patch_content,
                files_changed=patch_result.files_changed,
                explanation=patch_result.explanation,
            )
            db.add(repair)
            await db.commit()
            await db.refresh(repair)

            await event_broadcaster.broadcast(analysis_id, "PATCH_GENERATED", {
                "repair_id": repair.id,
                "files_changed": repair.files_changed,
            })

            # ==========================================
            # STAGE 5: PATCH VALIDATION
            # ==========================================
            analysis.current_stage = "PATCH_VALIDATION"
            await db.commit()
            await event_broadcaster.broadcast(analysis_id, "STAGE_CHANGED", {"stage": "PATCH_VALIDATION"})

            manifest_paths = [f["path"] for f in repo_meta["files"]]
            is_valid, validation_errors = PatchValidator.validate_patch(
                patch_text=repair.patch_content,
                repo_dir=repo_storage_dir,
                allowed_manifest_paths=manifest_paths
            )

            # ==========================================
            # STAGE 6: ISOLATED TEST EXECUTION
            # ==========================================
            analysis.current_stage = "TEST_EXECUTION"
            await db.commit()
            await event_broadcaster.broadcast(analysis_id, "STAGE_CHANGED", {"stage": "TEST_EXECUTION"})

            # Create isolated workspace copy
            sandbox_root = settings.get_sandbox_path()
            isolated_workspace = sandbox_root / f"analysis_{analysis_id}_repair_{repair.id}"
            PatchApplier.create_isolated_copy(repo_storage_dir, isolated_workspace)

            # Apply patch to isolated copy
            apply_success, apply_msg, files_modified = PatchApplier.apply_patch_in_workspace(
                isolated_workspace,
                repair.patch_content
            )

            if apply_success:
                repair.status = "applied"
                repair.applied_at = datetime.now(timezone.utc)
                await db.commit()

            # Run tests on patched isolated copy
            patched_test_results = TestRunnerService.execute_pytest(
                isolated_workspace,
                timeout=settings.SANDBOX_TIMEOUT_SECONDS
            )

            test_exec = TestExecution(
                repair_id=repair.id,
                status=patched_test_results.status,
                total_tests=patched_test_results.total,
                passed_tests=patched_test_results.passed,
                failed_tests=patched_test_results.failed,
                skipped_tests=patched_test_results.skipped,
                execution_duration=patched_test_results.duration,
                stdout=patched_test_results.raw_stdout,
                stderr=patched_test_results.raw_stderr,
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
            )
            db.add(test_exec)
            await db.commit()

            # ==========================================
            # STAGE 7: REGRESSION CHECK
            # ==========================================
            analysis.current_stage = "REGRESSION_CHECK"
            await db.commit()
            await event_broadcaster.broadcast(analysis_id, "STAGE_CHANGED", {"stage": "REGRESSION_CHECK"})

            if baseline_test_results:
                regression_diff = RegressionComparator.compare(baseline_test_results, patched_test_results)
            else:
                regression_diff = {
                    "has_regression": False,
                    "is_improved": patched_test_results.status == "passed",
                    "fixed_tests": [],
                    "new_regressions": [],
                    "still_failing": [],
                }

            # ==========================================
            # STAGE 8: FINAL VERIFICATION DECISION & REPORT
            # ==========================================
            analysis.current_stage = "VERIFICATION"
            await db.commit()
            await event_broadcaster.broadcast(analysis_id, "STAGE_CHANGED", {"stage": "VERIFICATION"})

            decision = VerificationDecisionEngine.evaluate(
                patch_applied_cleanly=apply_success,
                syntax_valid=is_valid,
                test_results=patched_test_results.to_dict(),
                regression_diff=regression_diff,
                has_tests=has_tests,
                security_passed=is_valid,
            )

            # Generate 11-section structured report
            report_content = VerificationReportGenerator.generate_report_content(
                bug_data={
                    "title": target_bug.title,
                    "category": target_bug.category,
                    "severity": target_bug.severity,
                    "file_path": target_bug.file_path,
                    "line_number": target_bug.line_number,
                    "description": target_bug.description,
                    "root_cause": target_bug.root_cause,
                    "evidence": target_bug.evidence,
                    "confidence": target_bug.confidence,
                },
                repair_data={
                    "patch_content": repair.patch_content,
                    "files_changed": repair.files_changed,
                    "explanation": repair.explanation,
                },
                test_data=patched_test_results.to_dict(),
                regression_diff=regression_diff,
                decision=decision,
            )

            v_report = VerificationReport(
                repair_id=repair.id,
                status=decision["status"],
                checks_performed=decision["checks_performed"],
                checks_passed=decision["checks_passed"],
                checks_failed=decision["checks_failed"],
                remaining_risks=decision["remaining_risks"],
                report_content=report_content,
            )
            db.add(v_report)

            # Update repair status based on verification
            repair.status = "verified" if decision["status"] == "VERIFIED" else "failed"

            # Update analysis
            analysis.status = "COMPLETED"
            analysis.current_stage = "COMPLETED"
            analysis.completed_at = datetime.now(timezone.utc)
            await db.commit()

            # Cleanup sandbox workspace
            try:
                if isolated_workspace.exists():
                    shutil.rmtree(isolated_workspace)
            except Exception:
                pass

            # Log activity
            await log_activity(
                db=db,
                user_id=user_id,
                project_id=project_id,
                event_type="REPAIR_VERIFIED" if decision["status"] == "VERIFIED" else "ANALYSIS_COMPLETED",
                description=f"Analysis completed with verdict: {decision['status']}",
                metadata={"verdict": decision["status"], "repair_id": repair.id}
            )
            await db.commit()

            await event_broadcaster.broadcast(analysis_id, "COMPLETED", {
                "verdict": decision["status"],
                "repair_id": repair.id,
            })

        except Exception as e:
            analysis.status = "FAILED"
            analysis.error_message = str(e)
            await db.commit()
            await event_broadcaster.broadcast(analysis_id, "FAILED", {"error": str(e)})
            raise
