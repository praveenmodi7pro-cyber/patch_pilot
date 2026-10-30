# PatchPilot Deployment Guide

## 1. Local Development Quickstart

### Prerequisites
- Python 3.12+ (or Python 3.14)
- Node.js 20+ & npm

### Step 1: Clone and Configure Environment
```bash
git clone https://github.com/patchpilot/patchpilot.git
cd patch_pilot
cp .env.example .env
```

### Step 2: Backend Setup
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .\.venv\Scripts\activate
pip install -r backend/requirements.txt
```

### Step 3: Frontend Setup
```bash
cd frontend
npm install
cd ..
```

### Step 4: Run Services
Start the FastAPI backend:
```bash
python -m uvicorn app.main:app --app-dir backend --reload --port 8000
```

Start the Next.js frontend (in a separate terminal):
```bash
cd frontend
npm run dev
```

Visit `http://localhost:3000` in your browser.

---

## 2. Docker Compose Production Deployment

To launch the full production topology (PostgreSQL 16, Redis 7, FastAPI backend, Next.js frontend, and sandbox container):

```bash
docker compose up -d --build
```

### Health Checks
- Backend API health: `GET http://localhost:8000/health`
- Frontend UI: `http://localhost:3000`
- PostgreSQL: `pg_isready -U patchpilot -h localhost -p 5432`
- Redis: `redis-cli ping`

