# PatchPilot REST API Documentation

All endpoints are versioned under `/api/v1`.

## Authentication

### `POST /auth/register`
Create a new user account.
- **Request Body:** `{ "name": "string", "email": "user@domain.com", "password": "password123" }`
- **Response (201):** `{ "access_token": "string", "token_type": "bearer", "user": { ... } }`

### `POST /auth/login`
Authenticate user credentials. Sets HttpOnly session cookie and returns Bearer token.
- **Request Body:** `{ "email": "user@domain.com", "password": "password123" }`
- **Response (200):** Token payload.

### `GET /auth/me`
Get current authenticated user profile.
- **Headers:** `Authorization: Bearer <token>`
- **Response (200):** User object.

### `POST /auth/logout`
Invalidate cookie session.

---

## Projects

### `GET /projects`
List projects for the authenticated user.

### `POST /projects`
Create a new project entry.

### `POST /projects/upload` (Multipart)
Upload a `.zip` archive containing project source code.
- **Form Data:** `file` (ZIP binary), `name` (string), `description` (string)
- **Response (201):** Project object with indexed file count.

### `POST /projects/github/import`
Import repository from a GitHub URL.

### `GET /projects/{project_id}/files`
Get recursive file tree for Monaco explorer.

### `GET /projects/{project_id}/file?path=<path>`
Read individual source file content (scrubbed of secrets).

---

## Analysis & Real-Time Telemetry

### `POST /projects/{project_id}/analyze`
Trigger autonomous 8-stage AI debugging pipeline.
- **Response (201):** Analysis session object (`status: "QUEUED"`).

### `GET /analysis/{analysis_id}/status`
Get current stage, completion percentage, and stage history.

### `GET /analysis/{analysis_id}/bugs`
List all bugs discovered during analysis.

### `GET /analysis/{analysis_id}/events` (SSE)
Server-Sent Events stream for live pipeline updates (`STAGE_CHANGED`, `BUG_DETECTED`, `PATCH_GENERATED`, `COMPLETED`).

### `WS /analysis/{analysis_id}/ws`
WebSocket endpoint for real-time progress updates.

---

## Bugs & Repairs

### `GET /bugs/{bug_id}`
Get detailed diagnosis and evidence for a specific bug.

### `POST /bugs/{bug_id}/generate-repair`
Generate a minimal unified diff patch for this bug.

### `GET /repairs/{repair_id}`
Get repair metadata, patch diff, and files changed.

### `GET /repairs/{repair_id}/diff`
Get before-and-after source code for Monaco Diff Editor.

### `POST /repairs/{repair_id}/approve`
Approve proposed patch.

### `POST /repairs/{repair_id}/reject`
Reject proposed patch.

### `POST /repairs/{repair_id}/apply`
Apply patch to an isolated workspace copy.

### `GET /repairs/{repair_id}/download`
Download raw `.patch` file.

---

## Testing & Reports

### `POST /repairs/{repair_id}/test`
Execute test suite against patched isolated workspace in Docker sandbox.

### `GET /repairs/{repair_id}/tests`
List test execution history and raw stdout/stderr logs.

### `GET /repairs/{repair_id}/report`
Retrieve complete 11-section verification audit report JSON.

### `GET /repairs/{repair_id}/report/pdf`
Download official PDF verification report.

