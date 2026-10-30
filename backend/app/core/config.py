import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "PatchPilot"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    API_V1_PREFIX: str = "/api/v1"
    APP_SECRET_KEY: str = "b95a8f43c8d1976a4392b8cfd01e18ac4e3b7492cfa71e84a51e6d3c90b6a71e"
    
    # Token Settings
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    ALGORITHM: str = "HS256"
    
    # Database & Redis
    DATABASE_URL: str = "sqlite+aiosqlite:///./patchpilot.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # AI Configuration
    AI_PROVIDER: str = "mock"  # "mock", "gemini", "openai", "anthropic"
    AI_API_KEY: Optional[str] = None
    AI_MODEL: str = "gpt-4o-mini"
    AI_TIMEOUT_SECONDS: int = 60
    
    # GitHub Integration
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None
    GITHUB_CALLBACK_URL: str = "http://localhost:3000/auth/github/callback"
    
    # URLs and CORS
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    
    # Storage & Execution Limits
    MAX_UPLOAD_SIZE_MB: int = 50
    ANALYSIS_TIMEOUT_SECONDS: int = 300
    SANDBOX_TIMEOUT_SECONDS: int = 60
    SANDBOX_CPU_LIMIT: float = 1.0
    SANDBOX_MEMORY_LIMIT: str = "512m"
    STORAGE_PATH: str = "./storage"
    SANDBOX_WORKSPACE_PATH: str = "./sandboxes"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def get_storage_path(self) -> Path:
        p = Path(self.STORAGE_PATH)
        p.mkdir(parents=True, exist_ok=True)
        return p

    def get_sandbox_path(self) -> Path:
        p = Path(self.SANDBOX_WORKSPACE_PATH)
        p.mkdir(parents=True, exist_ok=True)
        return p


settings = Settings()

