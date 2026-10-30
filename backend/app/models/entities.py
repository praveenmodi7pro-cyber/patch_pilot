import uuid
from datetime import datetime, timezone
from typing import List, Optional, Any
from sqlalchemy import (
    String, Text, Integer, Float, Boolean, DateTime, ForeignKey, Index, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def generate_uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    projects: Mapped[List["Project"]] = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    activity_logs: Mapped[List["ActivityLog"]] = relationship("ActivityLog", back_populates="user", cascade="all, delete-orphan")
    github_connection: Mapped[Optional["GitHubConnection"]] = relationship("GitHubConnection", back_populates="user", uselist=False, cascade="all, delete-orphan")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_type: Mapped[str] = mapped_column(String(50), default="zip")  # "zip", "github"
    repository_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    repository_branch: Mapped[Optional[str]] = mapped_column(String(100), default="main")
    commit_sha: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    language: Mapped[str] = mapped_column(String(50), default="python")
    status: Mapped[str] = mapped_column(String(50), default="created")  # created, analyzing, analyzed, failed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    user: Mapped["User"] = relationship("User", back_populates="projects")
    files: Mapped[List["RepositoryFile"]] = relationship("RepositoryFile", back_populates="project", cascade="all, delete-orphan")
    analyses: Mapped[List["Analysis"]] = relationship("Analysis", back_populates="project", cascade="all, delete-orphan")
    activity_logs: Mapped[List["ActivityLog"]] = relationship("ActivityLog", back_populates="project", cascade="all, delete-orphan")


class RepositoryFile(Base):
    __tablename__ = "repository_files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    path: Mapped[str] = mapped_column(String(1000), nullable=False)
    language: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    size: Mapped[int] = mapped_column(Integer, default=0)
    checksum: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    indexed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    project: Mapped["Project"] = relationship("Project", back_populates="files")

    __table_args__ = (
        Index("idx_repo_files_proj_path", "project_id", "path"),
    )


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="QUEUED")  # QUEUED, INITIALIZING, COMPLETED, FAILED, CANCELLED
    current_stage: Mapped[str] = mapped_column(String(100), default="QUEUED")
    progress_metadata: Mapped[Optional[Any]] = mapped_column(JSON, default=dict)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    project: Mapped["Project"] = relationship("Project", back_populates="analyses")
    bugs: Mapped[List["Bug"]] = relationship("Bug", back_populates="analysis", cascade="all, delete-orphan", lazy="selectin")
    repairs: Mapped[List["Repair"]] = relationship("Repair", back_populates="analysis", cascade="all, delete-orphan", lazy="selectin")


class Bug(Base):
    __tablename__ = "bugs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    analysis_id: Mapped[str] = mapped_column(String(36), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[str] = mapped_column(String(100), default="runtime_error")  # syntax_error, runtime_error, logic_error, static_check
    severity: Mapped[str] = mapped_column(String(50), default="medium")  # critical, high, medium, low, informational
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    line_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    root_cause: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence: Mapped[Optional[Any]] = mapped_column(JSON, default=list)  # list of strings / tracebacks
    confidence: Mapped[float] = mapped_column(Float, default=0.85)
    status: Mapped[str] = mapped_column(String(50), default="detected")  # detected, reviewed, repairing, repaired, dismissed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    analysis: Mapped["Analysis"] = relationship("Analysis", back_populates="bugs")
    repairs: Mapped[List["Repair"]] = relationship("Repair", back_populates="bug", cascade="all, delete-orphan")


class Repair(Base):
    __tablename__ = "repairs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    bug_id: Mapped[str] = mapped_column(String(36), ForeignKey("bugs.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_id: Mapped[str] = mapped_column(String(36), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="generated")  # generated, approved, rejected, applied, verified, failed
    original_commit: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    patch_content: Mapped[str] = mapped_column(Text, nullable=False)  # unified diff format
    files_changed: Mapped[Optional[Any]] = mapped_column(JSON, default=list)  # list of file paths
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    applied_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    bug: Mapped["Bug"] = relationship("Bug", back_populates="repairs")
    analysis: Mapped["Analysis"] = relationship("Analysis", back_populates="repairs")
    test_executions: Mapped[List["TestExecution"]] = relationship("TestExecution", back_populates="repair", cascade="all, delete-orphan")
    verification_reports: Mapped[List["VerificationReport"]] = relationship("VerificationReport", back_populates="repair", cascade="all, delete-orphan")


class TestExecution(Base):
    __tablename__ = "test_executions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    repair_id: Mapped[str] = mapped_column(String(36), ForeignKey("repairs.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="running")  # passed, failed, partially_passed, timed_out, error
    total_tests: Mapped[int] = mapped_column(Integer, default=0)
    passed_tests: Mapped[int] = mapped_column(Integer, default=0)
    failed_tests: Mapped[int] = mapped_column(Integer, default=0)
    skipped_tests: Mapped[int] = mapped_column(Integer, default=0)
    execution_duration: Mapped[float] = mapped_column(Float, default=0.0)  # seconds
    stdout: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    stderr: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    repair: Mapped["Repair"] = relationship("Repair", back_populates="test_executions")


class VerificationReport(Base):
    __tablename__ = "verification_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    repair_id: Mapped[str] = mapped_column(String(36), ForeignKey("repairs.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)  # VERIFIED, PARTIALLY_VERIFIED, FAILED, INCONCLUSIVE
    checks_performed: Mapped[Optional[Any]] = mapped_column(JSON, default=list)
    checks_passed: Mapped[Optional[Any]] = mapped_column(JSON, default=list)
    checks_failed: Mapped[Optional[Any]] = mapped_column(JSON, default=list)
    remaining_risks: Mapped[Optional[Any]] = mapped_column(JSON, default=list)
    report_content: Mapped[Optional[Any]] = mapped_column(JSON, default=dict)  # Complete 11-section report dictionary
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    repair: Mapped["Repair"] = relationship("Repair", back_populates="verification_reports")


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    event_metadata: Mapped[Optional[Any]] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    user: Mapped["User"] = relationship("User", back_populates="activity_logs")
    project: Mapped[Optional["Project"]] = relationship("Project", back_populates="activity_logs")


class GitHubConnection(Base):
    __tablename__ = "github_connections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    encrypted_access_token: Mapped[str] = mapped_column(Text, nullable=False)
    github_username: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    user: Mapped["User"] = relationship("User", back_populates="github_connection")
