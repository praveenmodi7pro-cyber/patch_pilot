import hashlib
import io
import os
import re
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Excluded directories and file patterns
EXCLUDED_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    "build",
    "dist",
    ".next",
    ".idea",
    ".vscode",
    ".pytest_cache",
    ".ruff_cache",
    "eggs",
    ".eggs",
}

EXCLUDED_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".so",
    ".dll",
    ".exe",
    ".bin",
    ".zip",
    ".tar",
    ".gz",
    ".7z",
    ".iso",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".mp4",
    ".mp3",
    ".wav",
    ".pdf",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
}

SECRET_PATTERNS = [
    (re.compile(r"(?i)aws_access_key_id\s*=\s*['\"]?([A-Z0-9]{20})['\"]?"), "[REDACTED_AWS_KEY]"),
    (re.compile(r"(?i)aws_secret_access_key\s*=\s*['\"]?([A-Za-z0-9/+=]{40})['\"]?"), "[REDACTED_AWS_SECRET]"),
    (re.compile(r"ghp_[a-zA-Z0-9]{36}"), "[REDACTED_GITHUB_TOKEN]"),
    (re.compile(r"gho_[a-zA-Z0-9]{36}"), "[REDACTED_GITHUB_OAUTH]"),
    (re.compile(r"(?i)password\s*[:=]\s*['\"][^'\"]+['\"]"), "password: '[REDACTED_PASSWORD]'"),
    (re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----[\s\S]+?-----END (?:RSA |EC )?PRIVATE KEY-----"), "[REDACTED_PRIVATE_KEY]"),
    (re.compile(r"(?i)secret_key\s*[:=]\s*['\"][^'\"]+['\"]"), "secret_key: '[REDACTED_SECRET]'"),
]

LANGUAGE_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".jsx": "javascript",
    ".tsx": "typescript",
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
    ".php": "php",
    ".html": "html",
    ".css": "css",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".md": "markdown",
    ".txt": "text",
    ".sh": "shell",
}


def redact_secrets(content: str) -> str:
    """Scrub sensitive credentials from source files before sending to AI or logging."""
    redacted = content
    for pattern, replacement in SECRET_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def compute_checksum(content_bytes: bytes) -> str:
    return hashlib.sha256(content_bytes).hexdigest()


class SafeArchiveExtractor:
    """Safely extracts ZIP archives, defending against Zip Slip and file-system attacks."""

    @staticmethod
    def extract_zip(zip_bytes: bytes, destination_dir: Path, max_uncompressed_bytes: int = 100 * 1024 * 1024) -> List[Path]:
        destination_dir = destination_dir.resolve()
        destination_dir.mkdir(parents=True, exist_ok=True)
        extracted_paths: List[Path] = []
        total_extracted_size = 0

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
            for member in archive.infolist():
                # Defend against Zip Slip (path traversal)
                target_path = (destination_dir / member.filename).resolve()
                if not str(target_path).startswith(str(destination_dir)):
                    raise ValueError(f"Path traversal detected in archive entry: {member.filename}")

                if member.is_dir():
                    target_path.mkdir(parents=True, exist_ok=True)
                    continue

                total_extracted_size += member.file_size
                if total_extracted_size > max_uncompressed_bytes:
                    raise ValueError("Archive exceeds uncompressed size threshold (Zip Bomb protection)")

                target_path.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member) as source, open(target_path, "wb") as target:
                    target.write(source.read())

                extracted_paths.append(target_path)

        return extracted_paths


class RepositoryAnalyzer:
    """Scans and indexes an extracted repository folder."""

    def __init__(self, repo_dir: Path):
        self.repo_dir = repo_dir.resolve()

    def scan(self) -> Dict[str, Any]:
        files_manifest: List[Dict[str, Any]] = []
        lang_counts: Dict[str, int] = {}
        manifest_files: List[str] = []
        test_files: List[str] = []

        for root, dirs, files in os.walk(self.repo_dir):
            # Prune excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

            for file_name in files:
                file_path = Path(root) / file_name
                rel_path = file_path.relative_to(self.repo_dir).as_posix()
                ext = file_path.suffix.lower()

                if ext in EXCLUDED_EXTENSIONS:
                    continue

                # Skip large files > 5MB
                try:
                    size = file_path.stat().st_size
                except OSError:
                    continue

                if size > 5 * 1024 * 1024:
                    continue

                language = LANGUAGE_EXTENSIONS.get(ext, "unknown")
                if language != "unknown":
                    lang_counts[language] = lang_counts.get(language, 0) + 1

                # Track manifests
                if file_name in {"requirements.txt", "pyproject.toml", "setup.py", "Pipfile", "pytest.ini", "tox.ini", "package.json"}:
                    manifest_files.append(rel_path)

                # Track test files
                if "test" in rel_path.lower() or file_name.startswith("test_") or file_name.endswith("_test.py"):
                    test_files.append(rel_path)

                # Compute checksum
                try:
                    with open(file_path, "rb") as f:
                        checksum = compute_checksum(f.read())
                except Exception:
                    checksum = None

                files_manifest.append({
                    "path": rel_path,
                    "language": language,
                    "size": size,
                    "checksum": checksum,
                })

        # Determine primary language
        primary_lang = "python"
        if lang_counts:
            primary_lang = max(lang_counts.items(), key=lambda x: x[1])[0]

        return {
            "primary_language": primary_lang,
            "languages": lang_counts,
            "manifest_files": manifest_files,
            "test_files": test_files,
            "files": files_manifest,
            "total_files": len(files_manifest),
        }

    def build_file_tree(self) -> List[Dict[str, Any]]:
        """Construct a hierarchical file tree for Monaco and file browser."""
        root_nodes: Dict[str, Any] = {}

        for root, dirs, files in os.walk(self.repo_dir):
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
            for file_name in files:
                file_path = Path(root) / file_name
                rel_path = file_path.relative_to(self.repo_dir).as_posix()
                ext = file_path.suffix.lower()
                if ext in EXCLUDED_EXTENSIONS:
                    continue

                parts = rel_path.split("/")
                current = root_nodes
                for i, part in enumerate(parts):
                    is_last = (i == len(parts) - 1)
                    subpath = "/".join(parts[:i + 1])
                    if part not in current:
                        current[part] = {
                            "name": part,
                            "path": subpath,
                            "is_directory": not is_last,
                            "language": LANGUAGE_EXTENSIONS.get(ext, "unknown") if is_last else None,
                            "size": file_path.stat().st_size if is_last else None,
                            "children": {} if not is_last else None
                        }
                    if not is_last:
                        current = current[part]["children"]

        def convert_dict_to_list(nodes: Dict[str, Any]) -> List[Dict[str, Any]]:
            result = []
            # Folders first, then alphabetical
            sorted_items = sorted(nodes.values(), key=lambda x: (not x["is_directory"], x["name"].lower()))
            for item in sorted_items:
                node = {
                    "name": item["name"],
                    "path": item["path"],
                    "is_directory": item["is_directory"],
                    "language": item.get("language"),
                    "size": item.get("size"),
                }
                if item["children"] is not None:
                    node["children"] = convert_dict_to_list(item["children"])
                result.append(node)
            return result

        return convert_dict_to_list(root_nodes)

