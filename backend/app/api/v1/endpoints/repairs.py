import difflib
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.config import settings
from app.api.v1.deps import get_current_user
from app.models.entities import User, Project, Analysis, Bug, Repair
from app.schemas.schemas import RepairOut, RepairDiffOut
from app.services.activity import log_activity
from app.ai.factory import get_ai_provider
from app.ai.base import DiagnosisFinding
from app.repair.patch_applier import PatchApplier

router = APIRouter(prefix="/repairs", tags=["Repairs"])


@router.get("/{repair_id}", response_model=RepairOut)
async def get_repair(
    repair_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(Repair, Bug)
        .join(Bug, Repair.bug_id == Bug.id)
        .join(Analysis, Repair.analysis_id == Analysis.id)
        .join(Project, Analysis.project_id == Project.id)
        .where(Repair.id == repair_id, Project.user_id == current_user.id)
    )
    res = await db.execute(stmt)
    row = res.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repair not found")

    repair, bug = row
    r_out = RepairOut.model_validate(repair)
    r_out.bug_title = bug.title
    return r_out


@router.get("/{repair_id}/diff", response_model=RepairDiffOut)
async def get_repair_diff(
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

    diff_files = []
    for f_path in (repair.files_changed or []):
        file_disk = repo_dir / f_path
        original_code = ""
        if file_disk.exists():
            with open(file_disk, "r", encoding="utf-8", errors="replace") as f:
                original_code = f.read()

        # Parse modified lines from patch or simulate
        diff_files.append({
            "path": f_path,
            "original_code": original_code,
            "modified_code": original_code,  # Will be populated with patched preview
            "patch": repair.patch_content,
        })

    return RepairDiffOut(
        repair_id=repair.id,
        patch_content=repair.patch_content,
        files=diff_files,
        explanation=repair.explanation,
    )


@router.post("/{repair_id}/approve", response_model=RepairOut)
async def approve_patch(
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
    repair.status = "approved"
    repair.approved_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(repair)

    await log_activity(
        db=db,
        user_id=current_user.id,
        project_id=project.id,
        event_type="PATCH_APPROVED",
        description=f"Approved patch for repair {repair.id}",
        metadata={"repair_id": repair.id}
    )
    await db.commit()

    return RepairOut.model_validate(repair)


@router.post("/{repair_id}/reject", response_model=RepairOut)
async def reject_patch(
    repair_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(Repair)
        .join(Analysis, Repair.analysis_id == Analysis.id)
        .join(Project, Analysis.project_id == Project.id)
        .where(Repair.id == repair_id, Project.user_id == current_user.id)
    )
    res = await db.execute(stmt)
    repair = res.scalar_one_or_none()
    if not repair:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repair not found")

    repair.status = "rejected"
    await db.commit()
    await db.refresh(repair)
    return RepairOut.model_validate(repair)


@router.post("/{repair_id}/apply", response_model=RepairOut)
async def apply_patch_to_isolated_workspace(
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
    workspace = sandbox_root / f"apply_{repair.id}"
    PatchApplier.create_isolated_copy(repo_dir, workspace)

    success, msg, files = PatchApplier.apply_patch_in_workspace(workspace, repair.patch_content)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to apply patch: {msg}")

    repair.status = "applied"
    repair.applied_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(repair)

    return RepairOut.model_validate(repair)


@router.post("/{repair_id}/regenerate", response_model=RepairOut)
async def regenerate_patch(
    repair_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(Repair, Bug, Project)
        .join(Bug, Repair.bug_id == Bug.id)
        .join(Analysis, Repair.analysis_id == Analysis.id)
        .join(Project, Analysis.project_id == Project.id)
        .where(Repair.id == repair_id, Project.user_id == current_user.id)
    )
    res = await db.execute(stmt)
    row = res.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repair not found")

    repair, bug, project = row
    repo_dir = settings.get_storage_path() / project.id
    target_file = repo_dir / bug.file_path
    content = ""
    if target_file.exists():
        with open(target_file, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

    ai = get_ai_provider()
    new_patch = await ai.generate_patch(
        bug_finding=DiagnosisFinding(
            title=bug.title,
            category=bug.category,
            severity=bug.severity,
            file_path=bug.file_path,
            line_number=bug.line_number,
            root_cause=bug.root_cause or bug.description,
            evidence=bug.evidence or [],
            suggested_fix="Alternative patch formulation with stricter adherence to tests",
            confidence=bug.confidence,
        ),
        file_contents={bug.file_path: content},
        previous_feedback="Regenerate patch: user requested clean alternative formulation."
    )

    repair.patch_content = new_patch.patch_content
    repair.files_changed = new_patch.files_changed
    repair.explanation = new_patch.explanation
    repair.status = "generated"
    await db.commit()
    await db.refresh(repair)

    return RepairOut.model_validate(repair)


@router.get("/{repair_id}/download")
async def download_patch_file(
    repair_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(Repair)
        .join(Analysis, Repair.analysis_id == Analysis.id)
        .join(Project, Analysis.project_id == Project.id)
        .where(Repair.id == repair_id, Project.user_id == current_user.id)
    )
    res = await db.execute(stmt)
    repair = res.scalar_one_or_none()
    if not repair:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repair not found")

    filename = f"patchpilot_repair_{repair.id[:8]}.patch"
    return PlainTextResponse(
        content=repair.patch_content,
        media_type="text/x-diff",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

