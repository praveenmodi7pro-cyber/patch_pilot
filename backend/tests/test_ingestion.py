import io
import zipfile
import pytest
from pathlib import Path
from app.analysis.ingestion import SafeArchiveExtractor, redact_secrets
from app.analysis.ast_scanner import ASTCodeScanner
from app.repair.patch_validator import PatchValidator


def test_redact_secrets():
    content = """
    AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
    AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    token = "ghp_123456789012345678901234567890123456"
    password = 'super_secret_password'
    """
    redacted = redact_secrets(content)
    assert "AKIAIOSFODNN7EXAMPLE" not in redacted
    assert "[REDACTED_AWS_KEY]" in redacted
    assert "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY" not in redacted
    assert "[REDACTED_AWS_SECRET]" in redacted
    assert "ghp_" not in redacted
    assert "[REDACTED_GITHUB_TOKEN]" in redacted


def test_zip_slip_protection(tmp_path: Path):
    # Construct a malicious ZIP with path traversal
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        zf.writestr("../../etc/evil.txt", "malicious payload")

    target_dir = tmp_path / "extracted"

    with pytest.raises(ValueError, match="Path traversal detected"):
        SafeArchiveExtractor.extract_zip(zip_buffer.getvalue(), target_dir)


def test_ast_scanner_detects_syntax_and_dangerous_calls(tmp_path: Path):
    bad_code = """
def evil():
    eval("2 + 2")
    exec("import os")
"""
    file_path = tmp_path / "bad.py"
    file_path.write_text(bad_code, encoding="utf-8")

    findings = ASTCodeScanner.scan_file(file_path, "bad.py")
    categories = [f["category"] for f in findings]
    assert "security_risk" in categories
    assert any("eval" in f["title"] for f in findings)


def test_patch_validator_blocks_traversal_and_forbidden_calls(tmp_path: Path):
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    valid_file = repo_dir / "app.py"
    valid_file.write_text("def hello(): pass\n", encoding="utf-8")

    # 1. Malicious patch attempting to escape repo
    evil_patch = """--- a/../../secret.txt
+++ b/../../secret.txt
@@ -0,0 +1,1 @@
+stolen
"""
    valid, errors = PatchValidator.validate_patch(evil_patch, repo_dir, ["app.py"])
    assert not valid
    assert any("traversal" in e.lower() or "outside repository" in e.lower() for e in errors)

    # 2. Patch inserting eval()
    insecure_patch = """--- a/app.py
+++ b/app.py
@@ -1,1 +1,2 @@
+eval('os.system("rm -rf /")')
 def hello(): pass
"""
    valid, errors = PatchValidator.validate_patch(insecure_patch, repo_dir, ["app.py"])
    assert not valid
    assert any("Forbidden" in e for e in errors)

