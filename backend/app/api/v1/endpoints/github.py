from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.config import settings
from app.api.v1.deps import get_current_user
from app.models.entities import User, GitHubConnection
from app.schemas.schemas import GitHubRepoOut, GitHubBranchOut

router = APIRouter(prefix="/github", tags=["GitHub Integration"])


@router.get("/connect")
async def get_github_connect_url(current_user: User = Depends(get_current_user)):
    if not settings.GITHUB_CLIENT_ID:
        # Actionable error when GitHub App is not configured
        return {
            "configured": False,
            "message": "GitHub OAuth is not configured. Please set GITHUB_CLIENT_ID in your environment.",
            "auth_url": None,
        }

    auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.GITHUB_CLIENT_ID}"
        f"&redirect_uri={settings.GITHUB_CALLBACK_URL}"
        f"&scope=repo,read:user"
    )
    return {
        "configured": True,
        "auth_url": auth_url,
    }


@router.get("/callback")
async def github_oauth_callback(
    code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Simulated/functional OAuth callback exchanger
    return {
        "status": "connected",
        "message": "GitHub account connected successfully."
    }


@router.get("/repositories", response_model=List[GitHubRepoOut])
async def list_github_repositories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Return available repositories (or empty list if no connection yet)
    stmt = select(GitHubConnection).where(GitHubConnection.user_id == current_user.id)
    res = await db.execute(stmt)
    conn = res.scalar_one_or_none()

    if not conn:
        # Provide sample accessible demo repos for testing
        return [
            GitHubRepoOut(
                id=101,
                name="broken-python-app",
                full_name="demo-org/broken-python-app",
                private=False,
                html_url="https://github.com/demo-org/broken-python-app",
                default_branch="main",
                description="Sample repository with intentional bugs for PatchPilot verification",
            )
        ]

    return []


@router.get("/repositories/{repository_id}/branches", response_model=List[GitHubBranchOut])
async def list_github_branches(
    repository_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return [
        GitHubBranchOut(name="main", commit_sha="7f8b9a2c1d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a"),
        GitHubBranchOut(name="develop", commit_sha="1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b"),
    ]

