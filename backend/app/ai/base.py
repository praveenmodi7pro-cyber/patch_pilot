from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class DiagnosisFinding(BaseModel):
    title: str = Field(..., description="Concise bug title")
    category: str = Field(..., description="syntax_error, runtime_error, logic_error, static_check")
    severity: str = Field(..., description="critical, high, medium, low, informational")
    file_path: str = Field(..., description="Relative path to affected file")
    line_number: Optional[int] = Field(None, description="Line number of root cause")
    root_cause: str = Field(..., description="In-depth analysis of why this error happens")
    evidence: List[str] = Field(default_factory=list, description="Tracebacks, code excerpts or linter output")
    suggested_fix: str = Field(..., description="High-level solution strategy")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    verification_plan: List[str] = Field(default_factory=list, description="Plan to test and verify the fix")


class RootCauseAnalysisResult(BaseModel):
    findings: List[DiagnosisFinding]
    summary: str
    tokens_used: int = 0
    model: str = "unknown"


class GeneratedPatchResult(BaseModel):
    patch_content: str = Field(..., description="Unified git diff patch")
    files_changed: List[str] = Field(default_factory=list, description="List of modified files")
    explanation: str = Field(..., description="Step-by-step reason for the modifications")
    tokens_used: int = 0
    model: str = "unknown"


class BaseAIProvider(ABC):
    """Abstract Base Class for AI Debugging Providers."""

    def __init__(self, model_name: str, api_key: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key

    @abstractmethod
    async def analyze_root_cause(
        self,
        repository_context: Dict[str, Any],
        static_findings: List[Dict[str, Any]],
        test_failures: Optional[List[Dict[str, Any]]] = None,
    ) -> RootCauseAnalysisResult:
        """Perform root cause analysis on repository and detected issues."""
        pass

    @abstractmethod
    async def generate_patch(
        self,
        bug_finding: DiagnosisFinding,
        file_contents: Dict[str, str],
        previous_feedback: Optional[str] = None,
    ) -> GeneratedPatchResult:
        """Generate a minimal unified Git diff to repair the identified bug."""
        pass

