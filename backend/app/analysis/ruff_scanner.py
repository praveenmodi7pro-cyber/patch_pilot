import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any


class RuffScanner:
    """Executes Ruff static analysis and returns structured diagnostics."""

    @staticmethod
    def scan_directory(base_dir: Path) -> List[Dict[str, Any]]:
        findings: List[Dict[str, Any]] = []

        # Find ruff executable
        ruff_executable = shutil.which("ruff")
        if not ruff_executable:
            # Check virtualenv scripts
            venv_ruff = Path(sys.prefix) / ("Scripts" if sys.platform == "win32" else "bin") / ("ruff.exe" if sys.platform == "win32" else "ruff")
            if venv_ruff.exists():
                ruff_executable = str(venv_ruff)

        if not ruff_executable:
            return findings

        try:
            cmd = [
                ruff_executable,
                "check",
                str(base_dir),
                "--output-format=json",
                "--no-cache",
                "--exit-zero"
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                check=False
            )

            if result.stdout:
                try:
                    data = json.loads(result.stdout)
                    for item in data:
                        raw_filename = item.get("filename", "")
                        try:
                            rel_path = Path(raw_filename).relative_to(base_dir).as_posix()
                        except ValueError:
                            rel_path = raw_filename

                        code = item.get("code", "")
                        message = item.get("message", "")
                        location = item.get("location", {})
                        line_no = location.get("row", 1)

                        # Determine severity based on ruff code
                        severity = "low"
                        category = "static_check"
                        if code.startswith("E9") or code.startswith("F82") or code.startswith("F83"):
                            severity = "critical"
                            category = "syntax_error"
                        elif code.startswith("F"):  # Pyflakes errors (undefined names, imports)
                            severity = "high"
                            category = "runtime_error"
                        elif code.startswith("E") or code.startswith("W"):
                            severity = "medium"

                        findings.append({
                            "file_path": rel_path,
                            "line_number": line_no,
                            "category": category,
                            "severity": severity,
                            "title": f"[{code}] {message}",
                            "description": f"Static linter rule {code}: {message}",
                            "evidence": [f"Code: {code}", f"Location: line {line_no}"],
                        })
                except json.JSONDecodeError:
                    pass
        except Exception:
            pass

        return findings

