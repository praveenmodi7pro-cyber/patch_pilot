import io
import shutil
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.core.database import get_db
from app.core.config import settings
from app.api.v1.deps import get_current_user
from app.models.entities import User, Project, RepositoryFile, Analysis, Bug, Repair
from app.schemas.schemas import (
    ProjectCreate,
    ProjectUpdate,
    ProjectOut,
    FileTreeNode,
    FileContentOut,
    GitHubImportRequest,
)
from app.services.activity import log_activity
from app.analysis.ingestion import SafeArchiveExtractor, RepositoryAnalyzer, redact_secrets

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("", response_model=List[ProjectOut])
async def list_projects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(Project)
        .where(Project.user_id == current_user.id)
        .order_by(desc(Project.created_at))
    )
    result = await db.execute(stmt)
    projects = result.scalars().all()

    output = []
    for p in projects:
        # Get counts
        bugs_count = await db.scalar(
            select(func.count(Bug.id))
            .join(Analysis, Bug.analysis_id == Analysis.id)
            .where(Analysis.project_id == p.id)
        ) or 0

        repairs_count = await db.scalar(
            select(func.count(Repair.id))
            .join(Analysis, Repair.analysis_id == Analysis.id)
            .where(Analysis.project_id == p.id)
        ) or 0

        last_analysis = await db.scalar(
            select(Analysis.status)
            .where(Analysis.project_id == p.id)
            .order_by(desc(Analysis.created_at))
            .limit(1)
        )

        p_out = ProjectOut.model_validate(p)
        p_out.detected_bugs_count = bugs_count
        p_out.generated_patches_count = repairs_count
        p_out.last_analysis_status = last_analysis
        output.append(p_out)

    return output


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = Project(
        user_id=current_user.id,
        name=payload.name,
        description=payload.description,
        source_type=payload.source_type,
        repository_url=payload.repository_url,
        repository_branch=payload.repository_branch,
        language=payload.language,
        status="created",
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)

    await log_activity(
        db=db,
        user_id=current_user.id,
        project_id=project.id,
        event_type="PROJECT_CREATED",
        description=f"Created project '{project.name}'",
    )
    await db.commit()

    return ProjectOut.model_validate(project)


@router.post("/sample", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def load_sample_project(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """One-click loader for the built-in broken Python sample project."""
    candidate_paths = [
        Path.cwd() / "sample_projects" / "broken_python_app.zip",
        Path(__file__).resolve().parents[4] / "sample_projects" / "broken_python_app.zip",
        Path(__file__).resolve().parents[5] / "sample_projects" / "broken_python_app.zip",
    ]
    sample_zip = next((p for p in candidate_paths if p.exists()), None)
    if not sample_zip or not sample_zip.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sample broken project archive not found."
        )

    with open(sample_zip, "rb") as f:
        zip_bytes = f.read()

    project = Project(
        user_id=current_user.id,
        name="Broken Python App (Demo)",
        description="Pre-packaged test application with 3 intentional bugs (syntax, runtime zero-division, and discount logic).",
        source_type="sample",
        language="python",
        status="uploaded",
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)

    target_dir = settings.get_storage_path() / project.id

    try:
        SafeArchiveExtractor.extract_zip(zip_bytes, target_dir)
        analyzer = RepositoryAnalyzer(target_dir)
        manifest = analyzer.scan()

        for f in manifest["files"]:
            db.add(RepositoryFile(
                project_id=project.id,
                path=f["path"],
                language=f["language"],
                size=f["size"],
                checksum=f["checksum"],
            ))

        await db.commit()
    except Exception as e:
        if target_dir.exists():
            shutil.rmtree(target_dir)
        await db.delete(project)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to load sample project: {str(e)}"
        )

    await log_activity(
        db=db,
        user_id=current_user.id,
        project_id=project.id,
        event_type="PROJECT_UPLOADED",
        description=f"Loaded built-in sample project '{project.name}' ({manifest['total_files']} files)",
    )
    await db.commit()

    p_out = ProjectOut.model_validate(project)
    p_out.detected_bugs_count = 0
    p_out.generated_patches_count = 0
    return p_out


@router.post("/upload", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def upload_project_zip(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be a valid .zip archive."
        )

    zip_bytes = await file.read()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(zip_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Archive size exceeds maximum allowed limit of {settings.MAX_UPLOAD_SIZE_MB}MB."
        )

    project_name = name or Path(file.filename).stem or "Uploaded Project"

    # Create project record
    project = Project(
        user_id=current_user.id,
        name=project_name,
        description=description or f"Uploaded from {file.filename}",
        source_type="zip",
        language="python",
        status="uploaded",
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)

    target_dir = settings.get_storage_path() / project.id

    try:
        SafeArchiveExtractor.extract_zip(zip_bytes, target_dir)
        analyzer = RepositoryAnalyzer(target_dir)
        manifest = analyzer.scan()

        project.language = manifest["primary_language"]

        # If archive had a top-level single wrapper directory, move files up if appropriate
        sub_items = list(target_dir.iterdir())
        if len(sub_items) == 1 and sub_items[0].is_dir() and sub_items[0].name not in {".git", "tests", "app", "src"}:
            wrapper = sub_items[0]
            for item in wrapper.iterdir():
                shutil.move(str(item), str(target_dir))
            shutil.rmtree(wrapper)
            analyzer = RepositoryAnalyzer(target_dir)
            manifest = analyzer.scan()
            project.language = manifest["primary_language"]

        # Store repository files
        for f in manifest["files"]:
            db.add(RepositoryFile(
                project_id=project.id,
                path=f["path"],
                language=f["language"],
                size=f["size"],
                checksum=f["checksum"],
            ))

        await db.commit()
    except Exception as e:
        if target_dir.exists():
            shutil.rmtree(target_dir)
        await db.delete(project)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process archive: {str(e)}"
        )

    await log_activity(
        db=db,
        user_id=current_user.id,
        project_id=project.id,
        event_type="PROJECT_UPLOADED",
        description=f"Uploaded ZIP archive for project '{project.name}' ({manifest['total_files']} files indexed)",
    )
    await db.commit()

    p_out = ProjectOut.model_validate(project)
    p_out.detected_bugs_count = 0
    p_out.generated_patches_count = 0
    return p_out


@router.post("/github/import", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def import_github_repository(
    payload: GitHubImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Basic URL validation for SSRF protection
    repo_url = payload.repository_url.strip()
    if not (repo_url.startswith("https://github.com/") or repo_url.startswith("git@github.com:")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Repository URL must be a valid GitHub URL."
        )

    repo_name = payload.name or repo_url.rstrip("/").split("/")[-1].replace(".git", "")

    project = Project(
        user_id=current_user.id,
        name=repo_name,
        description=payload.description or f"Imported from {repo_url}",
        source_type="github",
        repository_url=repo_url,
        repository_branch=payload.branch,
        language="python",
        status="imported",
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)

    # Initialize empty target dir
    target_dir = settings.get_storage_path() / project.id
    target_dir.mkdir(parents=True, exist_ok=True)

    await log_activity(
        db=db,
        user_id=current_user.id,
        project_id=project.id,
        event_type="GITHUB_IMPORTED",
        description=f"Imported GitHub repository '{project.name}'",
    )
    await db.commit()

    return ProjectOut.model_validate(project)


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Project).where(Project.id == project_id, Project.user_id == current_user.id)
    res = await db.execute(stmt)
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    bugs_count = await db.scalar(
        select(func.count(Bug.id))
        .join(Analysis, Bug.analysis_id == Analysis.id)
        .where(Analysis.project_id == project.id)
    ) or 0

    repairs_count = await db.scalar(
        select(func.count(Repair.id))
        .join(Analysis, Repair.analysis_id == Analysis.id)
        .where(Analysis.project_id == project.id)
    ) or 0

    last_analysis = await db.scalar(
        select(Analysis.status)
        .where(Analysis.project_id == project.id)
        .order_by(desc(Analysis.created_at))
        .limit(1)
    )

    p_out = ProjectOut.model_validate(project)
    p_out.detected_bugs_count = bugs_count
    p_out.generated_patches_count = repairs_count
    p_out.last_analysis_status = last_analysis
    return p_out


@router.patch("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: str,
    payload: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Project).where(Project.id == project_id, Project.user_id == current_user.id)
    res = await db.execute(stmt)
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if payload.name is not None:
        project.name = payload.name
    if payload.description is not None:
        project.description = payload.description

    await db.commit()
    await db.refresh(project)
    return ProjectOut.model_validate(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Project).where(Project.id == project_id, Project.user_id == current_user.id)
    res = await db.execute(stmt)
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    # Cleanup storage
    target_dir = settings.get_storage_path() / project.id
    if target_dir.exists():
        try:
            shutil.rmtree(target_dir)
        except OSError:
            pass

    await db.delete(project)
    await db.commit()
    return None


@router.get("/{project_id}/files")
async def get_project_files(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Project).where(Project.id == project_id, Project.user_id == current_user.id)
    res = await db.execute(stmt)
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    repo_dir = settings.get_storage_path() / project.id
    if not repo_dir.exists():
        return []

    analyzer = RepositoryAnalyzer(repo_dir)
    return analyzer.build_file_tree()


@router.get("/{project_id}/file", response_model=FileContentOut)
async def get_project_file_content(
    project_id: str,
    path: str = Query(..., description="Relative path of file"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Project).where(Project.id == project_id, Project.user_id == current_user.id)
    res = await db.execute(stmt)
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    repo_dir = (settings.get_storage_path() / project.id).resolve()
    target_file = (repo_dir / path).resolve()

    # Path traversal protection
    if not str(target_file).startswith(str(repo_dir)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: path outside repository.")

    if not target_file.exists() or not target_file.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    try:
        with open(target_file, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to read file: {str(e)}")

    # Redact secrets before returning
    safe_content = redact_secrets(content)

    ext = target_file.suffix.lower()
    lang = "python" if ext == ".py" else ("javascript" if ext in {".js", ".jsx"} else "text")

    return FileContentOut(
        path=path,
        language=lang,
        content=safe_content,
        size=target_file.stat().st_size,
    )

