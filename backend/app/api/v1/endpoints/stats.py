from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.models.entities import User, Project, Analysis, Bug, Repair, ActivityLog
from app.schemas.schemas import DashboardStatsOut, ActivityLogOut

router = APIRouter(prefix="/stats", tags=["Statistics & Activity"])


@router.get("/dashboard", response_model=DashboardStatsOut)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Total projects
    total_projects = await db.scalar(
        select(func.count(Project.id)).where(Project.user_id == current_user.id)
    ) or 0

    # Total debugging sessions (analyses)
    total_analyses = await db.scalar(
        select(func.count(Analysis.id))
        .join(Project, Analysis.project_id == Project.id)
        .where(Project.user_id == current_user.id)
    ) or 0

    # Bugs detected
    bugs_detected = await db.scalar(
        select(func.count(Bug.id))
        .join(Analysis, Bug.analysis_id == Analysis.id)
        .join(Project, Analysis.project_id == Project.id)
        .where(Project.user_id == current_user.id)
    ) or 0

    # Repairs verified
    repairs_verified = await db.scalar(
        select(func.count(Repair.id))
        .join(Analysis, Repair.analysis_id == Analysis.id)
        .join(Project, Analysis.project_id == Project.id)
        .where(Project.user_id == current_user.id, Repair.status == "verified")
    ) or 0

    # Repairs awaiting review (generated or applied)
    repairs_awaiting_review = await db.scalar(
        select(func.count(Repair.id))
        .join(Analysis, Repair.analysis_id == Analysis.id)
        .join(Project, Analysis.project_id == Project.id)
        .where(Project.user_id == current_user.id, Repair.status.in_(["generated", "applied"]))
    ) or 0

    return DashboardStatsOut(
        total_projects=total_projects,
        total_debugging_sessions=total_analyses,
        bugs_detected=bugs_detected,
        repairs_verified=repairs_verified,
        repairs_awaiting_review=repairs_awaiting_review,
    )


@router.get("/activity", response_model=List[ActivityLogOut])
async def get_recent_activity(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(ActivityLog)
        .where(ActivityLog.user_id == current_user.id)
        .order_by(desc(ActivityLog.created_at))
        .limit(25)
    )
    res = await db.execute(stmt)
    logs = res.scalars().all()
    return [ActivityLogOut.model_validate(l) for l in logs]

