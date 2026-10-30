from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.config import settings
from app.api.v1.deps import get_current_user
from app.models.entities import User, Project, Analysis, Bug, Repair
from app.schemas.schemas import BugOut, BugUpdate, RepairOut
from app.ai.factory import get_ai_provider
from app.ai.base import DiagnosisFinding

router = APIRouter(prefix="/bugs", tags=["Bugs"])


@router.get("/{bug_id}", response_model=BugOut)
async def get_bug(
    bug_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(Bug)
        .join(Analysis, Bug.analysis_id == Analysis.id)
        .join(Project, Analysis.project_id == Project.id)
        .where(Bug.id == bug_id, Project.user_id == current_user.id)
    )
    res = await db.execute(stmt)
    bug = res.scalar_one_or_none()
    if not bug:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bug not found")

    return BugOut.model_validate(bug)


@router.patch("/{bug_id}", response_model=BugOut)
async def update_bug(
    bug_id: str,
    payload: BugUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(Bug)
        .join(Analysis, Bug.analysis_id == Analysis.id)
        .join(Project, Analysis.project_id == Project.id)
        .where(Bug.id == bug_id, Project.user_id == current_user.id)
    )
    res = await db.execute(stmt)
    bug = res.scalar_one_or_none()
    if not bug:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bug not found")

    if payload.status:
        bug.status = payload.status

    await db.commit()
    await db.refresh(bug)
    return BugOut.model_validate(bug)


@router.post("/{bug_id}/generate-repair", response_model=RepairOut, status_code=status.HTTP_201_CREATED)
async def generate_repair_for_bug(
    bug_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(Bug, Analysis, Project)
        .join(Analysis, Bug.analysis_id == Analysis.id)
        .join(Project, Analysis.project_id == Project.id)
        .where(Bug.id == bug_id, Project.user_id == current_user.id)
    )
    res = await db.execute(stmt)
    row = res.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bug not found")

    bug, analysis, project = row

    repo_dir = settings.get_storage_path() / project.id
    target_file = repo_dir / bug.file_path
    file_content = ""
    if target_file.exists():
        with open(target_file, "r", encoding="utf-8", errors="replace") as f:
            file_content = f.read()

    ai = get_ai_provider()
    patch_result = await ai.generate_patch(
        bug_finding=DiagnosisFinding(
            title=bug.title,
            category=bug.category,
            severity=bug.severity,
            file_path=bug.file_path,
            line_number=bug.line_number,
            root_cause=bug.root_cause or bug.description,
            evidence=bug.evidence or [],
            suggested_fix="Fix the bug while strictly adhering to code structure",
            confidence=bug.confidence,
        ),
        file_contents={bug.file_path: file_content}
    )

    repair = Repair(
        bug_id=bug.id,
        analysis_id=analysis.id,
        status="generated",
        patch_content=patch_result.patch_content,
        files_changed=patch_result.files_changed,
        explanation=patch_result.explanation,
    )
    db.add(repair)
    bug.status = "repairing"
    await db.commit()
    await db.refresh(repair)

    r_out = RepairOut.model_validate(repair)
    r_out.bug_title = bug.title
    return r_out

