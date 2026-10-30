from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ==========================================
# AUTH & USER SCHEMAS
# ==========================================

class UserBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


class UserOut(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[int] = None


# ==========================================
# REPOSITORY & FILE SCHEMAS
# ==========================================

class RepositoryFileOut(BaseModel):
    id: str
    project_id: str
    path: str
    language: Optional[str] = None
    size: int
    checksum: Optional[str] = None
    indexed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FileContentOut(BaseModel):
    path: str
    language: str
    content: str
    size: int


class FileTreeNode(BaseModel):
    name: str
    path: str
    is_directory: bool
    children: Optional[List["FileTreeNode"]] = None
    size: Optional[int] = None
    language: Optional[str] = None


# ==========================================
# PROJECT SCHEMAS
# ==========================================

class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    language: str = "python"


class ProjectCreate(ProjectBase):
    source_type: str = "zip"  # "zip", "github"
    repository_url: Optional[str] = None
    repository_branch: Optional[str] = "main"


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ProjectOut(ProjectBase):
    id: str
    user_id: str
    source_type: str
    repository_url: Optional[str] = None
    repository_branch: Optional[str] = None
    commit_sha: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    detected_bugs_count: Optional[int] = 0
    generated_patches_count: Optional[int] = 0
    last_analysis_status: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# BUG SCHEMAS
# ==========================================

class BugBase(BaseModel):
    title: str
    category: str  # syntax_error, runtime_error, logic_error, static_check
    severity: str  # critical, high, medium, low, informational
    file_path: str
    line_number: Optional[int] = None
    description: str
    root_cause: Optional[str] = None
    evidence: List[str] = []
    confidence: float = 0.85


class BugCreate(BugBase):
    analysis_id: str


class BugUpdate(BaseModel):
    status: Optional[str] = None  # reviewed, dismissed


class BugOut(BugBase):
    id: str
    analysis_id: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# REPAIR SCHEMAS
# ==========================================

class RepairBase(BaseModel):
    patch_content: str
    files_changed: List[str] = []
    explanation: Optional[str] = None


class RepairCreate(RepairBase):
    bug_id: str
    analysis_id: str


class RepairOut(RepairBase):
    id: str
    bug_id: str
    analysis_id: str
    status: str  # generated, approved, rejected, applied, verified, failed
    original_commit: Optional[str] = None
    approved_at: Optional[datetime] = None
    applied_at: Optional[datetime] = None
    created_at: datetime
    bug_title: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RepairDiffOut(BaseModel):
    repair_id: str
    patch_content: str
    files: List[Dict[str, Any]]
    explanation: Optional[str] = None


# ==========================================
# TEST EXECUTION SCHEMAS
# ==========================================

class TestExecutionOut(BaseModel):
    id: str
    repair_id: str
    status: str  # passed, failed, partially_passed, timed_out, error
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    execution_duration: float
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# VERIFICATION REPORT SCHEMAS
# ==========================================

class VerificationReportOut(BaseModel):
    id: str
    repair_id: str
    status: str  # VERIFIED, PARTIALLY_VERIFIED, FAILED, INCONCLUSIVE
    checks_performed: List[str] = []
    checks_passed: List[str] = []
    checks_failed: List[str] = []
    remaining_risks: List[str] = []
    report_content: Dict[str, Any] = {}
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# ANALYSIS SCHEMAS
# ==========================================

class AnalysisCreate(BaseModel):
    project_id: str


class AnalysisOut(BaseModel):
    id: str
    project_id: str
    status: str
    current_stage: str
    progress_metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    bugs: List[BugOut] = []

    model_config = ConfigDict(from_attributes=True)


class AnalysisStatusOut(BaseModel):
    id: str
    project_id: str
    status: str
    current_stage: str
    progress_percentage: int = 0
    stages_completed: List[str] = []
    error_message: Optional[str] = None


# ==========================================
# DASHBOARD & ACTIVITY SCHEMAS
# ==========================================

class ActivityLogOut(BaseModel):
    id: str
    user_id: str
    project_id: Optional[str] = None
    event_type: str
    description: str
    event_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DashboardStatsOut(BaseModel):
    total_projects: int
    total_debugging_sessions: int
    bugs_detected: int
    repairs_verified: int
    repairs_awaiting_review: int


# ==========================================
# GITHUB SCHEMAS
# ==========================================

class GitHubRepoOut(BaseModel):
    id: int
    name: str
    full_name: str
    private: bool
    html_url: str
    default_branch: str
    description: Optional[str] = None


class GitHubBranchOut(BaseModel):
    name: str
    commit_sha: str


class GitHubImportRequest(BaseModel):
    repository_url: str
    branch: str = "main"
    name: Optional[str] = None
    description: Optional[str] = None
