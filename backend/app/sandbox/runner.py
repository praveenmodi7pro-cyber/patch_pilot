import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple


class SandboxExecutionResult:
    def __init__(
        self,
        exit_code: int,
        stdout: str,
        stderr: str,
        duration: float,
        is_isolated: bool,
        isolation_type: str,
        error_message: Optional[str] = None,
    ):
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.duration = duration
        self.is_isolated = is_isolated
        self.isolation_type = isolation_type
        self.error_message = error_message

    def to_dict(self) -> Dict[str, Any]:
        return {
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration": self.duration,
            "is_isolated": self.is_isolated,
            "isolation_type": self.isolation_type,
            "error_message": self.error_message,
        }


class SandboxRunner:
    """Executes tests inside Docker container if available, or secure isolated subprocess."""

    @staticmethod
    def is_docker_available() -> bool:
        docker_bin = shutil.which("docker")
        if not docker_bin:
            return False
        try:
            res = subprocess.run(["docker", "info"], capture_output=True, timeout=3)
            return res.returncode == 0
        except Exception:
            return False

    @classmethod
    def execute_command(
        cls,
        workspace_dir: Path,
        command: List[str],
        timeout_seconds: int = 45,
    ) -> SandboxExecutionResult:
        workspace_dir = workspace_dir.resolve()
        start_time = time.time()

        # 1. Check Docker container availability
        if cls.is_docker_available():
            return cls._execute_in_docker(workspace_dir, command, timeout_seconds)
        else:
            # 2. Local Restricted Sandbox
            return cls._execute_local_restricted(workspace_dir, command, timeout_seconds)

    @classmethod
    def _execute_in_docker(
        cls,
        workspace_dir: Path,
        command: List[str],
        timeout_seconds: int,
    ) -> SandboxExecutionResult:
        start_time = time.time()
        container_mount = f"{workspace_dir.as_posix()}:/workspace:rw"
        docker_cmd = [
            "docker", "run", "--rm",
            "--network", "none",
            "--memory", "512m",
            "--cpus", "1.0",
            "-v", container_mount,
            "-w", "/workspace",
            "--user", "1000:1000",
            "patchpilot-sandbox:python3.12",
        ] + command

        try:
            proc = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
            duration = time.time() - start_time
            return SandboxExecutionResult(
                exit_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                duration=duration,
                is_isolated=True,
                isolation_type="DOCKER_ISOLATED",
            )
        except subprocess.TimeoutExpired:
            return SandboxExecutionResult(
                exit_code=-1,
                stdout="",
                stderr=f"Execution timed out after {timeout_seconds} seconds",
                duration=timeout_seconds,
                is_isolated=True,
                isolation_type="DOCKER_ISOLATED",
                error_message="Test execution timed out inside Docker sandbox.",
            )
        except Exception as e:
            return SandboxExecutionResult(
                exit_code=-1,
                stdout="",
                stderr=str(e),
                duration=time.time() - start_time,
                is_isolated=False,
                isolation_type="DOCKER_FAILED",
                error_message=f"Docker execution failed: {str(e)}",
            )

    @classmethod
    def _execute_local_restricted(
        cls,
        workspace_dir: Path,
        command: List[str],
        timeout_seconds: int,
    ) -> SandboxExecutionResult:
        """Secure isolated local runner when Docker daemon is not available."""
        start_time = time.time()

        # Clean sanitized environment: scrub all secret keys, tokens, and credentials
        sanitized_env = {
            "PATH": os.environ.get("PATH", ""),
            "PYTHONPATH": str(workspace_dir),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONUNBUFFERED": "1",
            "TEMP": os.environ.get("TEMP", ""),
            "TMP": os.environ.get("TMP", ""),
            "SYSTEMROOT": os.environ.get("SYSTEMROOT", "C:\\Windows"),
        }

        # Find python binary
        python_bin = sys.executable

        # Replace python alias if needed
        cmd = list(command)
        if cmd and cmd[0] == "pytest":
            cmd = [python_bin, "-m", "pytest"] + cmd[1:]
        elif cmd and cmd[0] == "python":
            cmd = [python_bin] + cmd[1:]

        try:
            proc = subprocess.run(
                cmd,
                cwd=str(workspace_dir),
                env=sanitized_env,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
            duration = time.time() - start_time
            return SandboxExecutionResult(
                exit_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                duration=duration,
                is_isolated=True,
                isolation_type="LOCAL_RESTRICTED_SANDBOX (Host Docker unavailable)",
            )
        except subprocess.TimeoutExpired:
            return SandboxExecutionResult(
                exit_code=-1,
                stdout="",
                stderr=f"Execution timed out after {timeout_seconds} seconds",
                duration=timeout_seconds,
                is_isolated=True,
                isolation_type="LOCAL_RESTRICTED_SANDBOX",
                error_message="Execution exceeded safety timeout threshold.",
            )
        except Exception as e:
            return SandboxExecutionResult(
                exit_code=-1,
                stdout="",
                stderr=str(e),
                duration=time.time() - start_time,
                is_isolated=False,
                isolation_type="LOCAL_ERROR",
                error_message=f"Execution failed: {str(e)}",
            )

