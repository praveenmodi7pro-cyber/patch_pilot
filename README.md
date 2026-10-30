# PatchPilot

> **Detect. Repair. Test. Verify.**  
> Autonomous AI Software Debugging and Verified Code Repair Platform.

PatchPilot is an autonomous AI-powered software engineering platform that analyzes broken software repositories, investigates root causes, synthesizes code repairs, executes automated tests in isolated sandboxes, and verifies whether the proposed fixes actually work.

---

## The Core Product Principle

**A generated code suggestion is not a verified solution.**

Unlike conventional chat assistants that guess solutions without testing them, PatchPilot enforces an unequivocal distinction between:

```text
[✓] Bug Detected
[✓] Root Cause Identified
[✓] Patch Generated
[✓] Patch Applied in Isolated Working Copy
[✓] Automated Tests Executed
[✓] Regressions Checked
[✓] Repair Formally Verified
```

A repair is never presented as successful unless the corresponding verification checks have actually executed and passed.

---

## Key Features

1. **AI-Powered Bug Detection & Root Cause Analysis:** Correlates Python AST structures, Ruff static diagnostics, and baseline test execution logs with structured Pydantic schemas.
2. **Minimal Unified Git Diffs:** Generates minimal patches that respect existing project architecture, conventions, and dependencies without gratuitous refactoring.
3. **Patch Validation Defense:** Validates diff structure, rejects file modifications outside repository bounds, guards against dangerous calls, and checks syntax.
4. **Isolated Sandbox Execution:** Uploaded code executes strictly within isolated sandbox environments (Docker or sandboxed runner) with non-root privileges, restricted memory/CPU, and zero outbound network egress.
5. **Automated Regression Detection:** Compares test results before and after patch application to identify newly failing tests.
6. **11-Section Audit Reports & PDF Export:** Comprehensive reports covering original issues, root causes, unified diffs, test logs, regression comparisons, remaining risks, and downloadable PDF audits.
7. **Developer-First UI:** Dark-first design system inspired by Linear, Vercel, and GitHub, equipped with Monaco Code and Diff editors, file trees, and real-time stage progress streaming via Server-Sent Events.

---

## Technology Stack

- **Frontend:** Next.js 14 (App Router), React 18, TypeScript (Strict Mode), Tailwind CSS, Monaco Editor, Lucide Icons.
- **Backend:** Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2.0 (Async), Alembic, ReportLab, Ruff, Pytest.
- **Database:** PostgreSQL (Production) / SQLite (Local Dev & Automated CI).
- **AI Abstraction Layer:** Configurable provider supporting Google Gemini, OpenAI, Anthropic, or high-fidelity Deterministic Mock Provider for offline testing.
- **Infrastructure:** Docker Compose, isolated sandbox environments, Redis.

---

## Architecture

```text
                    USER
                     |
                     v
             NEXT.JS FRONTEND
                     |
                     v
               FASTAPI SERVER
                     |
          +----------+----------+
          |          |          |
          v          v          v
       AUTH       DATABASE    REDIS
          |          |          |
          |          |          v
          |          |      JOB QUEUE
          |          |          |
          |          |          v
          |          |     AI WORKER
          |          |          |
          |          |     REPOSITORY
          |          |      ANALYSIS
          |          |          |
          |          |          v
          |          |      AI ENGINE
          |          |          |
          |          |          v
          |          |     PATCH GENERATOR
          |          |          |
          |          |          v
          |          |     DOCKER SANDBOX
          |          |          |
          |          |          v
          |          |      TEST RUNNER
          |          |          |
          +----------+----------+
                     |
                     v
              VERIFICATION
                     |
                     v
               REPAIR REPORT
                     |
                     v
                FRONTEND
```

---

## Getting Started

### Prerequisites

- Python 3.12+ (or 3.14)
- Node.js 20+ & npm
- Git
- Docker (optional for containerized sandbox execution)

### 1. Clone & Environment Configuration

```bash
git clone https://github.com/patchpilot/patchpilot.git
cd patch_pilot
cp .env.example .env
```

### 2. Backend Installation

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .\.venv\Scripts\activate
pip install -r backend/requirements.txt
```

### 3. Frontend Installation

```bash
cd frontend
npm install
cd ..
```

### 4. Running the Application

In Terminal 1 (FastAPI Backend):
```bash
python -m uvicorn app.main:app --app-dir backend --reload --port 8000
```

In Terminal 2 (Next.js Frontend):
```bash
cd frontend
npm run dev
```

Open your browser to: **`http://localhost:3000`**

- **Pre-seeded Evaluation Account:**
  - Email: `demo@patchpilot.io`
  - Password: `PatchPilot123!`

---

## Verifying with Broken Python Sample Project

A sample repository with three intentional bugs is included under `sample_projects/broken_python_app`:

1. **Syntax Error:** `app/auth.py` (missing colon on function signature)
2. **Runtime Error:** `app/calculator.py` (unhandled division by zero in `divide`)
3. **Logic Error:** `app/discount_service.py` (adds discount instead of subtracting)

### Running the End-to-End Test Suite

Run the full automated test suite verifying everything from ZIP ingestion to patch generation, isolated execution, and PDF report creation:

```bash
pytest backend/tests -v
```

All 8 tests execute and verify:
- Safe archive extraction & Zip Slip protection
- Secret scanning & redaction
- AST code scanner & Ruff linter
- Patch validation & boundary checks
- End-to-end autonomous debugging pipeline on `broken_python_app.zip`
- Report generation and PDF compilation

---

## Docker Compose Deployment

To deploy the entire production stack using Docker:

```bash
docker compose up -d --build
```

Services started:
- `postgres`: PostgreSQL 16 database
- `redis`: Redis 7 alpine
- `backend`: FastAPI server on port 8000
- `frontend`: Next.js web application on port 3000

---

## Documentation Links

- [Architecture Guide](docs/architecture.md)
- [API Reference](docs/api.md)
- [Security Model & Threat Mitigations](docs/security.md)
- [Deployment Guide](docs/deployment.md)

---

## License

Apache-2.0

