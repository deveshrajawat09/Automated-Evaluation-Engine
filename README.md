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

Prerequisites: Node.js 20+, Python 3.11+, and optionally Docker Desktop.

For the complete local stack (PostgreSQL, Redis, API, sandbox runner, and
frontend), use Docker Compose:

```powershell
docker compose up --build
```

Open `http://localhost:5173`; the API is available at `http://localhost:8000`
and its docs at `http://localhost:8000/docs`. The backend container applies the
Alembic migration automatically on startup. Stop the stack with:

```powershell
docker compose down
```

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

The runner now accepts only an artifact identifier and structured test input.
It uses fixed Python, Node.js, Java, or C++ toolchains, never a caller-provided
shell command, and returns per-test stdout, stderr, exit code, and pass/fail
status. The source input volume is mounted read-only; build and execution
happen only inside the restricted runner container.

## Production follow-up

The MVP path is complete, including real GitHub analysis, validated AI-provider
responses, and a Docker-isolated runner. Before a public deployment:

1. Run the relational database migration with `cd backend; alembic upgrade head`.
2. Configure a permission-scoped `GITHUB_TOKEN` and an approved LLM provider.
3. Keep the sandbox as a separate rootless-container service; never attach the
   backend to a host Docker socket.
4. Replace local JSON uploads with object storage and asynchronous processing
   for pitch/video extraction.
5. Add deployment monitoring, secret rotation, rate limiting, and a managed
   PostgreSQL backup policy.

Authentication endpoints include an in-process rate limit for local and
single-instance deployments. Multi-instance deployments should move this
counter to Redis so all API replicas share the same limit.

The AI evaluation adapter accepts either the evaluation JSON object directly or an
OpenAI-compatible chat response whose first choice contains that JSON. Responses
are validated against the configured rubric and score bounds; invalid provider
responses are explicitly marked as `demo_fallback` rather than being persisted as
trusted evaluations.

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

### Google Cloud deployment

For a production deployment, use the supplied [Google Cloud infrastructure
configuration](./infra/gcp/README.md). It provisions Cloud Run services, private
Cloud SQL, Memorystore Redis, private versioned Cloud Storage, VPC access, and
Secret Manager bindings. The backend automatically uses Cloud Storage when
`GCS_BUCKET` is set and retains local disk storage for development.

Cloud integration checks are opt-in:

```powershell
$env:RUN_CLOUD_INTEGRATION_TESTS = "1"
$env:CLOUD_API_URL = "https://YOUR_BACKEND.run.app"
$env:CLOUD_FRONTEND_URL = "https://YOUR_FRONTEND.run.app"
cd backend
pytest -q tests/test_cloud_integration.py
```
