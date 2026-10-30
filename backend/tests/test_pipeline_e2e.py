from pathlib import Path
import pytest
from httpx import AsyncClient
from app.workers.pipeline import AnalysisPipelineRunner


@pytest.mark.asyncio
async def test_full_autonomous_debugging_pipeline(client: AsyncClient):
    # 1. Register user
    reg_res = await client.post("/api/v1/auth/register", json={
        "name": "QA Specialist",
        "email": "qa@patchpilot.io",
        "password": "SecurePassword123!",
    })
    assert reg_res.status_code == 201
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Upload broken sample project ZIP
    zip_path = Path(__file__).resolve().parent.parent.parent / "sample_projects" / "broken_python_app.zip"
    assert zip_path.exists(), f"Sample zip not found at {zip_path}"

    with open(zip_path, "rb") as zf:
        upload_res = await client.post(
            "/api/v1/projects/upload",
            headers=headers,
            files={"file": ("broken_python_app.zip", zf, "application/zip")},
            data={"name": "Broken Python App", "description": "Intentional 3-bug project"}
        )

    assert upload_res.status_code == 201
    project_data = upload_res.json()
    project_id = project_data["id"]

    # 3. Verify files were indexed
    files_res = await client.get(f"/api/v1/projects/{project_id}/files", headers=headers)
    assert files_res.status_code == 200
    file_tree = files_res.json()
    assert len(file_tree) > 0

    # 4. Read one file via API
    content_res = await client.get(
        f"/api/v1/projects/{project_id}/file?path=app/calculator.py",
        headers=headers
    )
    assert content_res.status_code == 200
    assert "def divide" in content_res.json()["content"]

    # 5. Start Analysis
    analyze_res = await client.post(f"/api/v1/projects/{project_id}/analyze", headers=headers)
    assert analyze_res.status_code == 201
    analysis_data = analyze_res.json()
    analysis_id = analysis_data["id"]

    # 6. Execute pipeline
    await AnalysisPipelineRunner.run_pipeline(analysis_id)

    # 7. Check Analysis Status
    status_res = await client.get(f"/api/v1/analysis/{analysis_id}/status", headers=headers)
    print("STATUS RES:", status_res.json())
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["status"] == "COMPLETED"

    # 8. Check Detected Bugs
    bugs_res = await client.get(f"/api/v1/analysis/{analysis_id}/bugs", headers=headers)
    assert bugs_res.status_code == 200
    bugs = bugs_res.json()
    assert len(bugs) > 0
    bug_titles = [b["title"] for b in bugs]

    # Verify at least one intentional bug was detected
    assert any("syntax" in t.lower() or "divide" in t.lower() or "auth" in t.lower() for t in bug_titles)

    # 9. Verify Generated Repair
    full_analysis = await client.get(f"/api/v1/analysis/{analysis_id}", headers=headers)
    assert full_analysis.status_code == 200

    # 10. Check Dashboard Statistics derived from DB
    stats_res = await client.get("/api/v1/stats/dashboard", headers=headers)
    assert stats_res.status_code == 200
    stats_data = stats_res.json()
    assert stats_data["total_projects"] >= 1
    assert stats_data["total_debugging_sessions"] >= 1
    assert stats_data["bugs_detected"] >= 1
