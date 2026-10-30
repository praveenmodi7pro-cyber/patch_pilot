# PatchPilot Architecture Documentation

## 1. System Overview

PatchPilot is an autonomous AI software debugging and verified repair platform designed around a single immutable principle:

> **A generated code suggestion is not a verified solution.**

PatchPilot decomposes the debugging lifecycle into specialized, observable stages rather than a monolithic generative prompt:

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

## 2. Core Subsystems

### 2.1 Next.js 14 Frontend

- **App Router Architecture:** Modular pages under `/app/` utilizing client components for real-time reactivity and Monaco Code / Diff editors.
- **Design System:** Linear / Vercel dark-first aesthetic (`#090D16` primary background, `#101827` secondary, `#141E2E` card surface, `#6366F1` indigo accent, `#06B6D4` cyan accent).
- **Telemetry & Updates:** Server-Sent Events (`/api/v1/analysis/{id}/events`) and WebSocket fallback for live stage streaming.

### 2.2 FastAPI Backend

- **Modular REST API:** Structured under `/api/v1` with typed Pydantic contracts and dependency injection.
- **Database Layer:** SQLAlchemy 2.0 async engine with SQLite (local dev) and PostgreSQL (production).
- **Security:** Argon2 password hashing, signed JWT session handling with HttpOnly cookies, Fernet encryption for access tokens.

### 2.3 The 8-Stage Autonomous AI Pipeline

1. **Repository Ingestion:** Safe ZIP extraction, Zip Slip / path traversal defense, file filtering, language detection, secret scanning and redaction.
2. **Static Code Analysis:** Python AST scanning for syntax and dangerous calls (`eval`, `exec`), plus Ruff static diagnostics.
3. **Bug & Root Cause Detection:** Execution of baseline unit tests to capture runtime failures, coupled with structured AI root cause analysis.
4. **Patch Formulation:** AI synthesis of minimal unified Git diffs preserving project architecture and conventions.
5. **Patch Validation:** Diff syntax check, repository manifest boundary verification, secret scrub, and post-patch AST syntax validation.
6. **Isolated Sandbox Execution:** Patch applied strictly to an isolated working copy; test execution performed inside an unprivileged Docker container or sandboxed runner with CPU, memory, and timeout limits.
7. **Regression Comparison:** Differential comparator comparing baseline failures vs patched failures. Detects newly introduced regressions.
8. **Verification Decision Engine:** Formal evaluation awarding `VERIFIED`, `PARTIALLY_VERIFIED`, `FAILED`, or `INCONCLUSIVE`. Generates an 11-section structured report and downloadable PDF.

