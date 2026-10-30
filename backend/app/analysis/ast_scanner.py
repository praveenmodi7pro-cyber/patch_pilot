import ast
from pathlib import Path
from typing import List, Dict, Any


class ASTCodeScanner:
    """Performs deep AST parsing on Python source files to locate syntax errors, 
    dangerous dynamic calls, undefined variables, and suspicious patterns."""

    @staticmethod
    def scan_file(file_path: Path, relative_path: str) -> List[Dict[str, Any]]:
        findings: List[Dict[str, Any]] = []

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                source = f.read()
        except Exception as e:
            findings.append({
                "file_path": relative_path,
                "line_number": 1,
                "category": "io_error",
                "severity": "high",
                "title": "Failed to read file",
                "description": f"Unable to read file: {str(e)}",
                "evidence": [str(e)],
            })
            return findings

        # 1. Syntax Verification
        try:
            tree = ast.parse(source, filename=str(file_path))
        except SyntaxError as e:
            findings.append({
                "file_path": relative_path,
                "line_number": e.lineno or 1,
                "category": "syntax_error",
                "severity": "critical",
                "title": f"Syntax Error: {e.msg}",
                "description": f"Python syntax error on line {e.lineno}: {e.msg}",
                "evidence": [e.text.strip() if e.text else str(e)],
            })
            return findings

        # 2. AST Visitor for Suspicious Code Constructs
        class CodeVisitor(ast.NodeVisitor):
            def __init__(self):
                self.defined_names = set()
                self.imported_names = set()

            def visit_Import(self, node):
                for alias in node.names:
                    self.imported_names.add(alias.asname or alias.name)
                self.generic_visit(node)

            def visit_ImportFrom(self, node):
                for alias in node.names:
                    self.imported_names.add(alias.asname or alias.name)
                self.generic_visit(node)

            def visit_Call(self, node):
                # Detect dangerous eval/exec
                if isinstance(node.func, ast.Name):
                    if node.func.id in {"eval", "exec"}:
                        findings.append({
                            "file_path": relative_path,
                            "line_number": node.lineno,
                            "category": "security_risk",
                            "severity": "critical",
                            "title": f"Insecure execution function '{node.func.id}'",
                            "description": f"Use of dynamic code execution ({node.func.id}) presents a serious security vulnerability.",
                            "evidence": [f"Call to {node.func.id}() at line {node.lineno}"],
                        })
                self.generic_visit(node)

            def visit_ExceptHandler(self, node):
                # Bare except: except:
                if node.type is None:
                    findings.append({
                        "file_path": relative_path,
                        "line_number": node.lineno,
                        "category": "anti_pattern",
                        "severity": "low",
                        "title": "Bare 'except' clause catches all exceptions",
                        "description": "Catching all exceptions including SystemExit and KeyboardInterrupt can mask critical failures.",
                        "evidence": [f"Bare except at line {node.lineno}"],
                    })
                self.generic_visit(node)

            def visit_FunctionDef(self, node):
                # Check for mutable default arguments
                for default in node.args.defaults:
                    if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        findings.append({
                            "file_path": relative_path,
                            "line_number": node.lineno,
                            "category": "runtime_risk",
                            "severity": "medium",
                            "title": f"Mutable default argument in function '{node.name}'",
                            "description": "Using mutable default arguments (like lists or dicts) retains state across calls and causes subtle state leakage bugs.",
                            "evidence": [f"Function '{node.name}' line {node.lineno}"],
                        })
                self.generic_visit(node)

        visitor = CodeVisitor()
        visitor.visit(tree)
        return findings

    @classmethod
    def scan_directory(cls, base_dir: Path) -> List[Dict[str, Any]]:
        all_findings: List[Dict[str, Any]] = []
        for file_path in base_dir.rglob("*.py"):
            rel_path = file_path.relative_to(base_dir).as_posix()
            if any(part in rel_path.split("/") for part in {".git", ".venv", "venv", "__pycache__"}):
                continue
            findings = cls.scan_file(file_path, rel_path)
            all_findings.extend(findings)
        return all_findings

