from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    projects,
    analysis,
    bugs,
    repairs,
    testing,
    reports,
    github,
    stats,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(projects.router)
api_router.include_router(analysis.router)
api_router.include_router(bugs.router)
api_router.include_router(repairs.router)
api_router.include_router(testing.router)
api_router.include_router(reports.router)
api_router.include_router(github.router)
api_router.include_router(stats.router)

