from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.models.entities import User, Project, Analysis, Repair, VerificationReport
from app.schemas.schemas import VerificationReportOut
from app.verification.report_generator import VerificationReportGenerator

router = APIRouter(prefix="/repairs", tags=["Reports"])


@router.get("/{repair_id}/report", response_model=VerificationReportOut)
async def get_verification_report(
    repair_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(VerificationReport)
        .join(Repair, VerificationReport.repair_id == Repair.id)
        .join(Analysis, Repair.analysis_id == Analysis.id)
        .join(Project, Analysis.project_id == Project.id)
        .where(VerificationReport.repair_id == repair_id, Project.user_id == current_user.id)
        .order_by(desc(VerificationReport.created_at))
    )
    res = await db.execute(stmt)
    report = res.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Verification report not found")

    return VerificationReportOut.model_validate(report)


@router.get("/{repair_id}/report/pdf")
async def download_verification_report_pdf(
    repair_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(VerificationReport, Repair, Project)
        .join(Repair, VerificationReport.repair_id == Repair.id)
        .join(Analysis, Repair.analysis_id == Analysis.id)
        .join(Project, Analysis.project_id == Project.id)
        .where(VerificationReport.repair_id == repair_id, Project.user_id == current_user.id)
        .order_by(desc(VerificationReport.created_at))
    )
    res = await db.execute(stmt)
    row = res.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Verification report not found")

    report, repair, project = row
    report_data = report.report_content or {}

    pdf_bytes = VerificationReportGenerator.generate_pdf(report_data, project_name=project.name)
    filename = f"patchpilot_verification_report_{repair_id[:8]}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

