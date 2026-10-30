from pathlib import Path
import pytest
from httpx import AsyncClient
from app.workers.pipeline import AnalysisPipelineRunner


@pytest.mark.asyncio
async def test_repairs_and_pdf_reports(client: AsyncClient):
    # Register user
    reg_res = await client.post("/api/v1/auth/register", json={
        "name": "Report Tester",
        "email": "report_test@patchpilot.io",
        "password": "SecurePassword123!",
    })
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Upload broken sample project ZIP
    zip_path = Path(__file__).resolve().parent.parent.parent / "sample_projects" / "broken_python_app.zip"
    with open(zip_path, "rb") as zf:
        upload_res = await client.post(
            "/api/v1/projects/upload",
            headers=headers,
            files={"file": ("broken_python_app.zip", zf, "application/zip")},
            data={"name": "Report Test App"}
        )
    project_id = upload_res.json()["id"]

    # Start analysis and run pipeline
    analyze_res = await client.post(f"/api/v1/projects/{project_id}/analyze", headers=headers)
    analysis_id = analyze_res.json()["id"]
    await AnalysisPipelineRunner.run_pipeline(analysis_id)

    # Get analysis to retrieve repair
    analysis_res = await client.get(f"/api/v1/analysis/{analysis_id}", headers=headers)
    assert analysis_res.status_code == 200

    # Get bugs
    bugs_res = await client.get(f"/api/v1/analysis/{analysis_id}/bugs", headers=headers)
    bugs = bugs_res.json()
    assert len(bugs) > 0
    bug_id = bugs[0]["id"]

    # Generate repair for bug
    gen_repair_res = await client.post(f"/api/v1/bugs/{bug_id}/generate-repair", headers=headers)
    assert gen_repair_res.status_code == 201
    repair_id = gen_repair_res.json()["id"]

    # Get diff
    diff_res = await client.get(f"/api/v1/repairs/{repair_id}/diff", headers=headers)
    assert diff_res.status_code == 200
    diff_data = diff_res.json()
    assert "patch_content" in diff_data
    assert len(diff_data["files"]) > 0

    # Download patch
    patch_download_res = await client.get(f"/api/v1/repairs/{repair_id}/download", headers=headers)
    assert patch_download_res.status_code == 200
    assert "--- a/" in patch_download_res.text or "+++" in patch_download_res.text

    # Approve patch
    approve_res = await client.post(f"/api/v1/repairs/{repair_id}/approve", headers=headers)
    assert approve_res.status_code == 200
    assert approve_res.json()["status"] == "approved"

    # Run tests on repair
    test_run_res = await client.post(f"/api/v1/repairs/{repair_id}/test", headers=headers)
    assert test_run_res.status_code == 201
    test_data = test_run_res.json()
    assert "status" in test_data

    # List tests for repair
    tests_list_res = await client.get(f"/api/v1/repairs/{repair_id}/tests", headers=headers)
    assert tests_list_res.status_code == 200
    assert len(tests_list_res.json()) >= 1

