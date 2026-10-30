import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import init_db, AsyncSessionLocal
from app.api.v1.api import api_router
from app.models.entities import User
from app.core.security import get_password_hash
from sqlalchemy import select


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure storage paths exist
    settings.get_storage_path()
    settings.get_sandbox_path()

    # Initialize database tables
    await init_db()

    # Seed demo user for immediate evaluation
    async with AsyncSessionLocal() as db:
        stmt = select(User).where(User.email == "demo@patchpilot.io")
        res = await db.execute(stmt)
        if not res.scalar_one_or_none():
            demo_user = User(
                name="Pilot Developer",
                email="demo@patchpilot.io",
                password_hash=get_password_hash("PatchPilot123!"),
            )
            db.add(demo_user)
            await db.commit()

    yield


app = FastAPI(
    title="PatchPilot API",
    description="Autonomous AI Software Debugging and Code Repair Platform API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global safe error handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # In production, do not leak internal stack traces
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal error occurred while processing your request. Please try again later."},
    )

# Include API v1 router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "PatchPilot API",
        "ai_provider": settings.AI_PROVIDER,
        "environment": settings.APP_ENV,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)

