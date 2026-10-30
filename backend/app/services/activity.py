from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.entities import ActivityLog


async def log_activity(
    db: AsyncSession,
    user_id: str,
    event_type: str,
    description: str,
    project_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> ActivityLog:
    """Record an audit and activity log entry."""
    entry = ActivityLog(
        user_id=user_id,
        project_id=project_id,
        event_type=event_type,
        description=description,
        event_metadata=metadata or {},
    )
    db.add(entry)
    await db.flush()
    return entry

