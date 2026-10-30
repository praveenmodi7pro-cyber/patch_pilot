import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from app.sandbox.runner import SandboxRunner, SandboxExecutionResult


class ParsedTestResults:
    def __init__(
        self,
        total: int,
        passed: int,
        failed: int,
        skipped: int,
        duration: float,
        failures: List[Dict[str, Any]],
        raw_stdout: str,
        raw_stderr: str,
        status: str,
    ):
        self.total = total
        self.passed = passed
        self.failed = failed
        self.skipped = skipped
        self.duration = duration
        self.failures = failures
        self.raw_stdout = raw_stdout
        self.raw_stderr = raw_stderr
        self.status = status

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "duration": self.duration,
            "failures": self.failures,
            "status": self.status,
            "raw_stdout": self.raw_stdout,
            "raw_stderr": self.raw_stderr,
        }


class TestRunnerService:
    """Executes automated tests in isolated sandboxes and parses output."""

    @classmethod
    def execute_pytest(cls, workspace_dir: Path, test_paths: Optional[List[str]] = None, timeout: int = 45) -> ParsedTestResults:
        workspace_dir = workspace_dir.resolve()
        cmd = ["pytest", "-v", "--tb=short"]
        if test_paths:
            cmd.extend(test_paths)

        result: SandboxExecutionResult = SandboxRunner.execute_command(
            workspace_dir=workspace_dir,
            command=cmd,
            timeout_seconds=timeout,
        )

        return cls._parse_pytest_output(result)

    @classmethod
    def _parse_pytest_output(cls, result: SandboxExecutionResult) -> ParsedTestResults:
        stdout = result.stdout or ""
        stderr = result.stderr or ""
        full_output = stdout + "\n" + stderr

        passed = 0
        failed = 0
        skipped = 0
        failures: List[Dict[str, Any]] = []

        # Parse summary line e.g. "== 2 passed, 1 failed in 0.12s =="
        summary_match = re.search(r"=+\s*(.*?)\s+in\s+([\d\.]+)s\s*=+", stdout)
        duration = result.duration

        if summary_match:
            summary_text = summary_match.group(1)
            try:
                duration = float(summary_match.group(2))
            except ValueError:
                pass

            p_m = re.search(r"(\d+)\s+passed", summary_text)
            if p_m:
                passed = int(p_m.group(1))

            f_m = re.search(r"(\d+)\s+failed", summary_text)
            if f_m:
                failed = int(f_m.group(1))

            s_m = re.search(r"(\d+)\s+skipped", summary_text)
            if s_m:
                skipped = int(s_m.group(1))

            e_m = re.search(r"(\d+)\s+error", summary_text)
            if e_m:
                failed += int(e_m.group(1))

        # Parse individual failure headers e.g. "FAILED tests/test_calc.py::test_divide"
        for line in stdout.splitlines():
            if line.startswith("FAILED "):
                test_spec = line.replace("FAILED ", "").strip().split(" - ")[0]
                failures.append({
                    "test_name": test_spec,
                    "error_message": line,
                    "traceback": stdout[:1000],
                })

        total = passed + failed + skipped
        if total == 0 and result.exit_code != 0:
            status = "error"
            failed = 1
            total = 1
        elif failed == 0 and passed > 0:
            status = "passed"
        elif failed > 0 and passed > 0:
            status = "partially_passed"
        elif failed > 0 and passed == 0:
            status = "failed"
        elif total == 0:
            status = "no_tests_found"
        else:
            status = "passed"

        return ParsedTestResults(
            total=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration=duration,
            failures=failures,
            raw_stdout=stdout,
            raw_stderr=stderr,
            status=status,
        )


class RegressionComparator:
    """Compares baseline and patched test runs to detect introduced regressions."""

    @staticmethod
    def compare(baseline: ParsedTestResults, patched: ParsedTestResults) -> Dict[str, Any]:
        baseline_failed_names = {f["test_name"] for f in baseline.failures}
        patched_failed_names = {f["test_name"] for f in patched.failures}

        # Fixed tests: failed in baseline, now passed in patched
        fixed_tests = list(baseline_failed_names - patched_failed_names)

        # Regressions: passed in baseline, now failed in patched
        new_regressions = list(patched_failed_names - baseline_failed_names)

        # Persistently failing
        still_failing = list(baseline_failed_names & patched_failed_names)

        has_regression = len(new_regressions) > 0
        is_improved = len(fixed_tests) > 0 and not has_regression

        return {
            "has_regression": has_regression,
            "is_improved": is_improved,
            "fixed_tests": fixed_tests,
            "new_regressions": new_regressions,
            "still_failing": still_failing,
            "baseline_passed": baseline.passed,
            "baseline_failed": baseline.failed,
            "patched_passed": patched.passed,
            "patched_failed": patched.failed,
        }

