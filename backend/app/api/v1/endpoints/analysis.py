import asyncio
import json
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.models.entities import User, Project, Analysis, Bug, Repair
from app.schemas.schemas import AnalysisOut, AnalysisStatusOut, BugOut
from app.services.activity import log_activity
from app.workers.queue import job_queue
from app.core.events import event_broadcaster

router = APIRouter(tags=["Analysis"])

STAGE_PROGRESS = {
    "QUEUED": 5,
    "INITIALIZING": 10,
    "REPOSITORY_SCANNING": 20,
    "STATIC_CODE_ANALYSIS": 35,
    "BUG_DETECTION": 50,
    "PATCH_GENERATION": 65,
    "PATCH_VALIDATION": 75,
    "TEST_EXECUTION": 85,
    "REGRESSION_CHECK": 92,
    "VERIFICATION": 98,
    "COMPLETED": 100,
    "FAILED": 100,
    "CANCELLED": 100,
}


@router.post("/projects/{project_id}/analyze", response_model=AnalysisOut, status_code=status.HTTP_201_CREATED)
async def start_analysis(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Project).where(Project.id == project_id, Project.user_id == current_user.id)
    res = await db.execute(stmt)
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    analysis = Analysis(
        project_id=project.id,
        status="QUEUED",
        current_stage="QUEUED",
        progress_metadata={},
    )
    db.add(analysis)
    project.status = "analyzing"
    await db.commit()
    await db.refresh(analysis)

    await log_activity(
        db=db,
        user_id=current_user.id,
        project_id=project.id,
        event_type="ANALYSIS_STARTED",
        description=f"Initiated AI debugging analysis for '{project.name}'",
        metadata={"analysis_id": analysis.id}
    )
    await db.commit()

    # Enqueue background execution
    job_queue.enqueue_analysis(analysis.id)

    return AnalysisOut.model_validate(analysis)


@router.get("/analysis/{analysis_id}", response_model=AnalysisOut)
async def get_analysis(
    analysis_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(Analysis)
        .options(selectinload(Analysis.bugs))
        .join(Project, Analysis.project_id == Project.id)
        .where(Analysis.id == analysis_id, Project.user_id == current_user.id)
    )
    res = await db.execute(stmt)
    analysis = res.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis session not found")

    return AnalysisOut.model_validate(analysis)


@router.get("/analysis/{analysis_id}/status", response_model=AnalysisStatusOut)
async def get_analysis_status(
    analysis_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(Analysis)
        .join(Project, Analysis.project_id == Project.id)
        .where(Analysis.id == analysis_id, Project.user_id == current_user.id)
    )
    res = await db.execute(stmt)
    analysis = res.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis session not found")

    pct = STAGE_PROGRESS.get(analysis.current_stage, 50)
    all_stages = list(STAGE_PROGRESS.keys())
    cur_idx = all_stages.index(analysis.current_stage) if analysis.current_stage in all_stages else 0
    completed_stages = all_stages[:cur_idx]

    return AnalysisStatusOut(
        id=analysis.id,
        project_id=analysis.project_id,
        status=analysis.status,
        current_stage=analysis.current_stage,
        progress_percentage=pct,
        stages_completed=completed_stages,
        error_message=analysis.error_message,
    )


@router.get("/analysis/{analysis_id}/bugs", response_model=List[BugOut])
async def get_analysis_bugs(
    analysis_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(Bug)
        .join(Analysis, Bug.analysis_id == Analysis.id)
        .join(Project, Analysis.project_id == Project.id)
        .where(Analysis.id == analysis_id, Project.user_id == current_user.id)
        .order_by(desc(Bug.created_at))
    )
    res = await db.execute(stmt)
    bugs = res.scalars().all()
    return [BugOut.model_validate(b) for b in bugs]


@router.post("/analysis/{analysis_id}/cancel")
async def cancel_analysis(
    analysis_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(Analysis)
        .join(Project, Analysis.project_id == Project.id)
        .where(Analysis.id == analysis_id, Project.user_id == current_user.id)
    )
    res = await db.execute(stmt)
    analysis = res.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")

    if analysis.status in {"COMPLETED", "FAILED"}:
        return {"message": "Analysis is already finished."}

    analysis.status = "CANCELLED"
    analysis.current_stage = "CANCELLED"
    await db.commit()
    await event_broadcaster.broadcast(analysis_id, "CANCELLED", {"message": "User cancelled analysis"})
    return {"message": "Analysis cancelled."}


@router.get("/analysis/{analysis_id}/events")
async def stream_analysis_events(analysis_id: str):
    """Server-Sent Events (SSE) stream for real-time analysis pipeline stage updates."""
    queue = event_broadcaster.subscribe_sse(analysis_id)

    async def event_generator():
        try:
            # Yield initial connection heartbeat
            yield f"event: connected\ndata: {json.dumps({'analysis_id': analysis_id})}\n\n"
            while True:
                # Wait for next event with a periodic keep-alive
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=15.0)
                    event_type = payload.get("event", "message")
                    data_str = json.dumps(payload.get("data", {}))
                    yield f"event: {event_type}\ndata: {data_str}\n\n"
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
        finally:
            event_broadcaster.unsubscribe_sse(analysis_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.websocket("/analysis/{analysis_id}/ws")
async def websocket_analysis_events(websocket: WebSocket, analysis_id: str):
    """WebSocket connection for bidirectional and low-latency stage streaming."""
    await event_broadcaster.connect_ws(analysis_id, websocket)
    try:
        while True:
            # Keep socket open and accept incoming ping/messages
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        event_broadcaster.disconnect_ws(analysis_id, websocket)
    except Exception:
        event_broadcaster.disconnect_ws(analysis_id, websocket)

