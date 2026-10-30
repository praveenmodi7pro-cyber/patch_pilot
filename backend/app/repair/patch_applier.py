import shutil
import subprocess
from pathlib import Path
from typing import List, Tuple, Dict, Any


class PatchApplier:
    """Safely creates an isolated working copy and applies unified diffs."""

    @staticmethod
    def create_isolated_copy(source_repo_dir: Path, target_workspace_dir: Path) -> Path:
        """Copies source repository to an isolated workspace without touching original."""
        target_workspace_dir = target_workspace_dir.resolve()
        if target_workspace_dir.exists():
            shutil.rmtree(target_workspace_dir)
        shutil.copytree(source_repo_dir, target_workspace_dir)
        return target_workspace_dir

    @classmethod
    def apply_patch_in_workspace(cls, workspace_dir: Path, patch_content: str) -> Tuple[bool, str, List[str]]:
        """Applies unified diff patch to repository workspace."""
        workspace_dir = workspace_dir.resolve()
        modified_files: List[str] = []

        # Try git apply first if repository has git
        patch_file = workspace_dir / ".patchpilot.patch"
        try:
            with open(patch_file, "w", encoding="utf-8", newline="\n") as f:
                f.write(patch_content)

            # Try git apply
            git_proc = subprocess.run(
                ["git", "apply", "--whitespace=nowarn", str(patch_file)],
                cwd=str(workspace_dir),
                capture_output=True,
                text=True,
                timeout=15
            )
            if git_proc.returncode == 0:
                # Find changed files from patch
                for line in patch_content.splitlines():
                    if line.startswith("+++ b/"):
                        modified_files.append(line[6:].strip())
                return True, "Patch applied successfully via git apply", modified_files
        except Exception:
            pass
        finally:
            if patch_file.exists():
                try:
                    patch_file.unlink()
                except OSError:
                    pass

        # Pure Python fallback unified diff parser & applier
        try:
            success, message, files = cls._apply_unified_diff_pure_python(workspace_dir, patch_content)
            return success, message, files
        except Exception as e:
            return False, f"Failed to apply patch: {str(e)}", []

    @staticmethod
    def _apply_unified_diff_pure_python(workspace_dir: Path, patch_text: str) -> Tuple[bool, str, List[str]]:
        """Pure Python fallback for unified diff application."""
        lines = patch_text.splitlines(keepends=True)
        i = 0
        modified_files: List[str] = []

        while i < len(lines):
            line = lines[i]
            if line.startswith("--- "):
                # Header found
                i += 1
                if i >= len(lines) or not lines[i].startswith("+++ "):
                    return False, "Malformed diff header", []
                
                target_rel_path = lines[i][4:].strip()
                if target_rel_path.startswith("b/"):
                    target_rel_path = target_rel_path[2:]
                i += 1

                target_file = workspace_dir / target_rel_path
                if not target_file.exists():
                    # Handle new file creation
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    original_lines = []
                else:
                    with open(target_file, "r", encoding="utf-8", errors="replace") as f:
                        original_lines = f.readlines()

                new_lines = []
                orig_idx = 0

                # Process hunks for this file
                while i < len(lines) and lines[i].startswith("@@"):
                    hunk_header = lines[i]
                    i += 1
                    # Parse hunk header: @@ -old_start,old_len +new_start,new_len @@
                    parts = hunk_header.split("@@")
                    coords = parts[1].strip().split()
                    old_coord = coords[0][1:]  # strip '-'
                    old_start = int(old_coord.split(",")[0])
                    
                    # Copy unaffected lines prior to this hunk
                    target_orig_idx = max(0, old_start - 1)
                    while orig_idx < target_orig_idx and orig_idx < len(original_lines):
                        new_lines.append(original_lines[orig_idx])
                        orig_idx += 1

                    # Read hunk lines
                    while i < len(lines) and not lines[i].startswith("@@") and not lines[i].startswith("--- "):
                        hunk_line = lines[i]
                        if hunk_line.startswith("+"):
                            new_lines.append(hunk_line[1:])
                        elif hunk_line.startswith("-"):
                            orig_idx += 1  # Skip removed line
                        elif hunk_line.startswith(" ") or hunk_line.strip() == "":
                            # Context line
                            if orig_idx < len(original_lines):
                                new_lines.append(original_lines[orig_idx])
                                orig_idx += 1
                            else:
                                new_lines.append(hunk_line[1:])
                        i += 1

                # Copy any remaining lines after all hunks
                while orig_idx < len(original_lines):
                    new_lines.append(original_lines[orig_idx])
                    orig_idx += 1

                # Write patched file
                with open(target_file, "w", encoding="utf-8", newline="\n") as f:
                    f.writelines(new_lines)
                modified_files.append(target_rel_path)
            else:
                i += 1

        if not modified_files:
            return False, "No valid unified diff hunks found in patch", []

        return True, "Patch applied successfully", modified_files

