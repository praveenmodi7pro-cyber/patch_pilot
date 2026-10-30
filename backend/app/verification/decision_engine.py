from typing import Dict, List, Any


class VerificationDecisionEngine:
    """Evaluates patch validity, test execution, and regression diffs to render an unequivocal verification verdict."""

    @classmethod
    def evaluate(
        cls,
        patch_applied_cleanly: bool,
        syntax_valid: bool,
        test_results: Dict[str, Any],
        regression_diff: Dict[str, Any],
        has_tests: bool,
        security_passed: bool = True,
    ) -> Dict[str, Any]:
        checks_performed: List[str] = [
            "Unified diff format validation",
            "Path traversal and manifest boundary check",
            "Post-patch Python AST syntax verification",
            "Security pattern and credentials scrub",
        ]
        checks_passed: List[str] = []
        checks_failed: List[str] = []
        remaining_risks: List[str] = []

        # 1. Diff application
        if patch_applied_cleanly:
            checks_passed.append("Patch applied cleanly to isolated working copy")
        else:
            checks_failed.append("Patch failed to apply cleanly")

        # 2. Syntax verification
        if syntax_valid:
            checks_passed.append("AST syntax verification succeeded without errors")
        else:
            checks_failed.append("AST syntax verification failed (syntax error detected)")

        # 3. Security
        if security_passed:
            checks_passed.append("No forbidden dynamic executions or credentials found")
        else:
            checks_failed.append("Forbidden calls or credential exposure detected")

        # 4. Tests
        if has_tests:
            checks_performed.append("Automated Pytest suite execution")
            checks_performed.append("Baseline vs Patched regression differential check")

            if test_results.get("status") == "passed":
                checks_passed.append(f"All {test_results.get('total', 0)} tests passed successfully")
            else:
                checks_failed.append(f"Tests failed: {test_results.get('failed', 0)} failures out of {test_results.get('total', 0)}")

            if regression_diff.get("has_regression"):
                checks_failed.append(f"Regressions introduced in {len(regression_diff.get('new_regressions', []))} tests")
            else:
                checks_passed.append("Zero test regressions detected")
        else:
            remaining_risks.append("Project contains no unit test suite; verification limited to static syntax and structural analysis")

        # Determine Final Verdict
        if not patch_applied_cleanly or not syntax_valid or not security_passed:
            status = "FAILED"
            remaining_risks.append("Patch cannot be used because code did not compile or failed security validation")
        elif has_tests:
            if test_results.get("status") == "passed" and not regression_diff.get("has_regression"):
                status = "VERIFIED"
            elif regression_diff.get("has_regression"):
                status = "FAILED"
                remaining_risks.append("Patch introduces regressions into previously passing tests")
            elif test_results.get("status") == "partially_passed":
                status = "PARTIALLY_VERIFIED"
                remaining_risks.append("Some tests remain unpassed")
            else:
                status = "FAILED"
        else:
            status = "INCONCLUSIVE"
            remaining_risks.append("Cannot verify runtime behavior without tests")

        return {
            "status": status,
            "checks_performed": checks_performed,
            "checks_passed": checks_passed,
            "checks_failed": checks_failed,
            "remaining_risks": remaining_risks,
        }

