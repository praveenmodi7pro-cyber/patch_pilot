from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.core.config import settings
from app.api.v1.deps import get_current_user
from app.models.entities import User, Project, Analysis, Repair, TestExecution
from app.schemas.schemas import TestExecutionOut
from app.repair.patch_applier import PatchApplier
from app.testing.test_runner import TestRunnerService

router = APIRouter(tags=["Testing"])


@router.post("/repairs/{repair_id}/test", response_model=TestExecutionOut, status_code=status.HTTP_201_CREATED)
async def run_tests_for_repair(
    repair_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(Repair, Project)
        .join(Analysis, Repair.analysis_id == Analysis.id)
        .join(Project, Analysis.project_id == Project.id)
        .where(Repair.id == repair_id, Project.user_id == current_user.id)
    )
    res = await db.execute(stmt)
    row = res.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repair not found")

    repair, project = row
    repo_dir = settings.get_storage_path() / project.id

    sandbox_root = settings.get_sandbox_path()
    isolated_workspace = sandbox_root / f"test_exec_{repair.id}"
    PatchApplier.create_isolated_copy(repo_dir, isolated_workspace)

    # Apply patch
    PatchApplier.apply_patch_in_workspace(isolated_workspace, repair.patch_content)

    # Run Pytest in sandbox
    test_results = TestRunnerService.execute_pytest(
        isolated_workspace,
        timeout=settings.SANDBOX_TIMEOUT_SECONDS
    )

    test_exec = TestExecution(
        repair_id=repair.id,
        status=test_results.status,
        total_tests=test_results.total,
        passed_tests=test_results.passed,
        failed_tests=test_results.failed,
        skipped_tests=test_results.skipped,
        execution_duration=test_results.duration,
        stdout=test_results.raw_stdout,
        stderr=test_results.raw_stderr,
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
    )
    db.add(test_exec)
    await db.commit()
    await db.refresh(test_exec)

    return TestExecutionOut.model_validate(test_exec)


@router.get("/repairs/{repair_id}/tests", response_model=List[TestExecutionOut])
async def list_repair_tests(
    repair_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(TestExecution)
        .join(Repair, TestExecution.repair_id == Repair.id)
        .join(Analysis, Repair.analysis_id == Analysis.id)
        .join(Project, Analysis.project_id == Project.id)
        .where(Repair.id == repair_id, Project.user_id == current_user.id)
        .order_by(desc(TestExecution.started_at))
    )
    res = await db.execute(stmt)
    records = res.scalars().all()
    return [TestExecutionOut.model_validate(t) for t in records]


@router.get("/tests/{test_execution_id}", response_model=TestExecutionOut)
async def get_test_execution(
    test_execution_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(TestExecution)
        .join(Repair, TestExecution.repair_id == Repair.id)
        .join(Analysis, Repair.analysis_id == Analysis.id)
        .join(Project, Analysis.project_id == Project.id)
        .where(TestExecution.id == test_execution_id, Project.user_id == current_user.id)
    )
    res = await db.execute(stmt)
    record = res.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test execution not found")

    return TestExecutionOut.model_validate(record)

