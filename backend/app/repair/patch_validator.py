import ast
import re
from pathlib import Path
from typing import List, Tuple, Dict, Any


class PatchValidationError(Exception):
    pass


class PatchValidator:
    """Validates unified diff patches before execution in sandbox."""

    FORBIDDEN_PATTERNS = [
        re.compile(r"\b(eval|exec)\s*\("),
        re.compile(r"__import__\s*\("),
        re.compile(r"\bos\.system\s*\("),
        re.compile(r"\bsubprocess\.(Popen|run|call)\b"),
        re.compile(r"ghp_[a-zA-Z0-9]{36}"),
        re.compile(r"(?i)aws_secret_access_key"),
    ]

    @classmethod
    def validate_patch(
        cls,
        patch_text: str,
        repo_dir: Path,
        allowed_manifest_paths: List[str],
    ) -> Tuple[bool, List[str]]:
        errors: List[str] = []

        if not patch_text or not patch_text.strip():
            return False, ["Patch content is completely empty."]

        # 1. Parse affected files from diff header
        files_affected: List[str] = []
        for line in patch_text.splitlines():
            if line.startswith("+++ b/"):
                filepath = line[6:].strip()
                files_affected.append(filepath)

        if not files_affected:
            # Check for alternative diff format
            for line in patch_text.splitlines():
                if line.startswith("+++ "):
                    filepath = line[4:].strip().lstrip("b/")
                    files_affected.append(filepath)

        if not files_affected:
            return False, ["Invalid Unified Diff format: missing '+++' target file header."]

        # 2. Check path traversal and manifest bounds
        for rel_path in files_affected:
            if ".." in rel_path or rel_path.startswith("/") or "\\" in rel_path:
                errors.append(f"Security error: Invalid path or path traversal in patch target '{rel_path}'.")

            # Must exist in allowed manifest or be a valid new file in repo
            full_path = (repo_dir / rel_path).resolve()
            if not str(full_path).startswith(str(repo_dir.resolve())):
                errors.append(f"Security error: Target path '{rel_path}' is outside repository root.")

        # 3. Scan added lines for forbidden calls or secrets
        for line in patch_text.splitlines():
            if line.startswith("+") and not line.startswith("+++"):
                added_code = line[1:]
                for pattern in cls.FORBIDDEN_PATTERNS:
                    if pattern.search(added_code):
                        errors.append(f"Forbidden security construct or exposed credential detected in patch: {pattern.pattern}")

        return len(errors) == 0, errors

    @staticmethod
    def validate_python_syntax(source_code: str, filename: str = "patch.py") -> Tuple[bool, str]:
        """Verify Python code syntax after patch application."""
        try:
            ast.parse(source_code, filename=filename)
            return True, "Valid syntax"
        except SyntaxError as e:
            return False, f"Syntax error at line {e.lineno}: {e.msg}"

