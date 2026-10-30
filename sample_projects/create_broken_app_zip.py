import os
import zipfile
from pathlib import Path


def create_zip():
    base_dir = Path(__file__).resolve().parent / "broken_python_app"
    zip_path = Path(__file__).resolve().parent / "broken_python_app.zip"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(base_dir):
            dirs[:] = [d for d in dirs if d not in {"__pycache__", ".pytest_cache"}]
            for file in files:
                if file.endswith(".pyc"):
                    continue
                file_path = Path(root) / file
                rel_path = file_path.relative_to(base_dir)
                zipf.write(file_path, rel_path)

    print(f"Created {zip_path} ({zip_path.stat().st_size} bytes)")


if __name__ == "__main__":
    create_zip()

