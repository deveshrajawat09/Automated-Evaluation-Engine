# HackEval AI

HackEval AI is an explainable, role-aware hackathon management and intelligent project-evaluation MVP. It is designed as a college major-project foundation: polished enough to demonstrate, modular enough to extend, and explicit about the boundaries of automated risk scoring.

## What is included

- Responsive organizer workspace with Overview, Hackathons, Submissions, Leaderboard, Analytics, and Settings screens.
- FastAPI REST service with JWT login/register, role checks, hackathon/team/submission flows, judge evaluation, audit events, live leaderboard data, and OpenAPI docs.
- Repository analysis, static-code-analysis, scoring, and fraud-risk service abstractions that return explainable output.
- Safe sandbox adapter: untrusted code is **never** run by the API process. It responds only through a separately configured isolated runner.
- Deterministic demo fallback for AI evaluation, explicitly returned as `model_mode: "demo_fallback"`. This can be swapped for an LLM service without changing the API callers.

## Project structure

```text
frontend/          React + TypeScript + Vite interface
backend/app/       FastAPI routers, schemas, security, and services
backend/tests/     Unit tests for core evaluation services
docker-compose.yml PostgreSQL service for production-style local setup
```

## Run locally

Prerequisites: Node.js 20+, Python 3.11+, and optionally Docker Desktop for PostgreSQL.

```powershell
# terminal 1 — API
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 8000

# terminal 2 — dashboard
cd frontend
npm install
npm run dev
```

Open the dashboard at `http://localhost:5173` and API docs at `http://localhost:8000/docs`.

### Demo accounts

| Role | Email |
| --- | --- |
| Organizer | host@hackeval.ai |
| Judge | judge@hackeval.ai |
| Participant | participant@hackeval.ai |
| Admin | admin@hackeval.ai |

Demo passwords are defined in `backend/app/store.py` for local development.

## Evaluation safety and transparency

Scores and fraud signals are decision support, not automatic decisions. Every evaluation contains criterion-level reasoning; every manual judge update writes an audit record. The `/api/sandbox/run` API refuses execution until `SANDBOX_RUNNER_URL` points to a purpose-built runner which enforces network isolation, read-only temporary filesystems, memory/CPU limits, process limits, and timeouts.

## Next implementation steps

1. Run the relational database migration with `cd backend; alembic upgrade head` before starting a PostgreSQL-backed deployment.
2. Add a GitHub API adapter using `GITHUB_TOKEN` and permission-scoped requests.
3. Plug an approved LLM provider into the evaluation service through `AI_API_KEY`.
4. Deploy the sandbox as a separate rootless-container service; do not attach the backend to a host Docker socket.
5. Add file object storage and asynchronous task processing for pitch/video extraction.

### PostgreSQL migrations

Set `DATABASE_URL` to the PostgreSQL connection string and apply the schema before
starting the API:

```powershell
cd backend
$env:DATABASE_URL = "postgresql+psycopg://hackeval:hackeval@localhost:5432/hackeval"
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

The relational schema stores users, hackathons, teams, submissions, uploads, and
audit logs in separate tables. The existing JSON file remains the local fallback
when `DATABASE_URL` is not configured.
