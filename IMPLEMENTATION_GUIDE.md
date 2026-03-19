# Cereborate — Implementation Guide

> For engineers setting up, running, extending, and deploying Cereborate.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (Docker)](#quick-start-docker)
3. [Local Development (without Docker)](#local-development-without-docker)
4. [Environment Variables](#environment-variables)
5. [Database Migrations](#database-migrations)
6. [Running Tests](#running-tests)
7. [Linting & Type Checking](#linting--type-checking)
8. [Architecture Overview](#architecture-overview)
9. [Key Patterns & Conventions](#key-patterns--conventions)
10. [LLM Configuration](#llm-configuration)
11. [Adding New Features](#adding-new-features)
12. [Production Deployment](#production-deployment)
13. [CI/CD Pipeline](#cicd-pipeline)
14. [Troubleshooting](#troubleshooting)

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Docker | 24+ | Full stack orchestration |
| Docker Compose | 2.20+ | Service management |
| Python | 3.12 | Backend (if running locally) |
| Node.js | 20+ | Frontend (if running locally) |
| uv | latest | Python package manager |
| git | any | Version control |

Optional (for GPU-accelerated production):
- NVIDIA GPU + CUDA 12+ (for vLLM)

---

## Quick Start (Docker)

```bash
# 1. Clone the repo
git clone <repo-url> cereborate
cd cereborate

# 2. Copy environment template
cp .env.example .env
# Edit .env and set JWT_SECRET and NEXTAUTH_SECRET at minimum

# 3. Start all services
make up

# 4. Run database migrations
make migrate

# 5. Pull LLM models into Ollama (takes a few minutes on first run)
make pull-models

# 6. Open the app
open http://localhost:3000
# API docs: http://localhost:8000/docs
```

Services started by `make up`:

| Service | Port | Description |
|---------|------|-------------|
| frontend | 3000 | Next.js app |
| backend | 8000 | FastAPI server |
| postgres | 5432 | PostgreSQL 16 + pgvector |
| redis | 6379 | Cache + Celery broker |
| ollama | 11434 | Local LLM runtime |
| celery-worker | — | Async task worker |
| celery-beat | — | Scheduled task scheduler |

---

## Local Development (without Docker)

### Backend

```bash
cd backend

# Install dependencies
uv sync

# Set env vars (copy from .env.example, point to local postgres/redis)
export DATABASE_URL=postgresql+asyncpg://cereborate:password@localhost:5432/cereborate
export REDIS_URL=redis://localhost:6379/0
export JWT_SECRET=dev-secret
export LLM_BACKEND=ollama
export LLM_BASE_URL=http://localhost:11434/v1

# Run migrations
uv run alembic upgrade head

# Start the API server
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# In another terminal: start the Celery worker
uv run celery -A app.tasks.celery_app worker --loglevel=info

# In another terminal: start Celery Beat (scheduled tasks)
uv run celery -A app.tasks.celery_app beat --loglevel=info
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Set env vars
export NEXTAUTH_URL=http://localhost:3000
export NEXTAUTH_SECRET=dev-secret
export NEXT_PUBLIC_API_URL=http://localhost:8000

# Start dev server
npm run dev
```

### CLI

```bash
cd backend
uv run cereborate --help

# Configure the CLI to point at your backend
uv run cereborate config set-url http://localhost:8000

# Start an interactive planning session
uv run cereborate plan
```

---

## Environment Variables

All variables are documented in `.env.example`. The critical ones:

### Required

| Variable | Example | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://cereborate:password@postgres:5432/cereborate` | PostgreSQL connection string |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection string |
| `JWT_SECRET` | `<random 32+ char string>` | Signs JWTs — **never reuse across environments** |
| `NEXTAUTH_SECRET` | `<random 32+ char string>` | Signs NextAuth sessions |
| `NEXTAUTH_URL` | `http://localhost:3000` | Canonical URL of the frontend |

### LLM

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_BACKEND` | `ollama` | `ollama` (dev) or `vllm` (prod) |
| `LLM_BASE_URL` | `http://ollama:11434/v1` | OpenAI-compatible API base URL |
| `LLM_PLANNING_MODEL` | `qwen3:8b` | Model for planning, reasoning, Q&A |
| `LLM_CLASSIFIER_MODEL` | `qwen3:1.7b` | Model for shareability classification |
| `LLM_EMBEDDING_MODEL` | `nomic-embed-text` | Model for vector embeddings |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_ENV` | `development` | `development` or `production` |
| `CORS_ORIGINS` | `http://localhost:3000` | Allowed CORS origins (comma-separated) |
| `APP_URL` | `http://localhost:3000` | Used in absolute URL generation |

---

## Database Migrations

Migrations live in `backend/alembic/versions/`. Each file is numbered sequentially (`0001_`, `0002_`, ...).

```bash
# Apply all pending migrations
make migrate                      # via Docker
uv run alembic upgrade head       # locally

# Roll back the last migration
uv run alembic downgrade -1

# Create a new migration
make revision msg="add_foo_table"
# or locally:
uv run alembic revision --autogenerate -m "add_foo_table"
```

### Current migration chain

| File | Tables |
|------|--------|
| `0001_create_auth_tables` | tenants, users, tenant_memberships |
| `0002_create_idea_tables` | ideas, idea_versions, idea_components, planning_sessions, budgets, budget_line_items |
| `0003_create_brain_tables` | idea_links, component_dependencies, consistency_flags |
| `0004_create_shareability_tables` | shareability_rules, access_grants |
| `0005_create_team_tables` | questions, answers, notifications |

> **Note:** The `embedding` columns (`vector(768)`) are added via raw SQL in each migration because Alembic's autogenerate does not handle pgvector natively. When adding new vector columns, use `op.execute("ALTER TABLE ... ADD COLUMN embedding vector(768)")`.

---

## Running Tests

```bash
# All tests (requires a test database)
make test

# With coverage
cd backend && uv run pytest tests/ -v --cov=app --cov-report=term-missing

# Single file
cd backend && uv run pytest tests/test_planning.py -v

# Single test
cd backend && uv run pytest tests/test_auth.py::test_register -v
```

Tests use a separate database (`cereborate_test`). The `conftest.py` creates and drops all tables for each test session. LLM calls are **not** mocked by default — if you want offline tests, set `LLM_BASE_URL` to a local stub or mock `LLMClient` in your fixture.

### Test database setup

```bash
# Create the test database (once)
docker compose exec postgres psql -U cereborate -c "CREATE DATABASE cereborate_test;"
docker compose exec postgres psql -U cereborate -d cereborate_test -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

---

## Linting & Type Checking

```bash
# Lint + fix
make format

# Lint only (no fixes)
make lint

# Individual tools
cd backend
uv run ruff check app/ cli/ tests/         # fast linter
uv run ruff format app/ cli/ tests/        # formatter
uv run mypy app/ cli/ --ignore-missing-imports  # type checker
```

Frontend:
```bash
cd frontend
npm run lint      # ESLint
npm run build     # also type-checks via tsc
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Planning Interface                                │
│  Next.js 14 (frontend) + FastAPI (backend/api/v1/)          │
│  - /plan/* : planning sessions (WebSocket chat)             │
│  - /ideas/* : idea CRUD + components + export               │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: The Brain                                         │
│  backend/app/services/                                      │
│  - embedding_service   : nomic-embed-text via Ollama/vLLM   │
│  - linking_service     : cross-idea semantic links          │
│  - dependency_service  : component DAG, cycle detection     │
│  - consistency_service : advisory flags (budget, deadlines) │
│  - shareability_service: LLM-scored tier classification     │
│  Celery tasks handle async/nightly processing               │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: Team Interface                                    │
│  /shared/* /questions /notifications /dependencies          │
│  - Tier-filtered idea browsing                              │
│  - Q&A with LLM-assisted answers                            │
│  - Cross-idea dependency auto-exposure                      │
└─────────────────────────────────────────────────────────────┘
           │
    LLM Backbone (Ollama / vLLM)
    PostgreSQL 16 + pgvector
    Redis 7
```

### Directory layout (backend)

```
backend/app/
├── main.py              # FastAPI app factory
├── config.py            # Pydantic Settings
├── deps.py              # DI: get_db(), get_current_user_id()
├── database.py          # AsyncSession factory
├── models/              # SQLAlchemy ORM models (one file per domain)
├── schemas/             # Pydantic request/response schemas
├── api/v1/              # Route handlers (thin — delegate to services)
├── services/            # Business logic
├── llm/                 # LLM client + Jinja2 prompt templates + schemas
└── tasks/               # Celery async + scheduled tasks
```

---

## Key Patterns & Conventions

### Multi-tenancy

Every model includes `tenant_id`. Every query **must** filter by `tenant_id`. Use the `_get_tenant_id()` helper in route handlers:

```python
async def _get_tenant_id(user_id: str, db: AsyncSession) -> uuid.UUID:
    membership = await db.scalar(
        select(TenantMembership).where(TenantMembership.user_id == uuid.UUID(user_id))
    )
    if not membership:
        raise HTTPException(status_code=400, detail="No tenant membership found")
    return membership.tenant_id
```

### Services pattern

All business logic lives in `app/services/`. Route handlers are thin:

```python
@router.post("/ideas/{idea_id}/components")
async def add_component(idea_id, data, user_id=Depends(...), db=Depends(get_db)):
    tenant_id = await _get_tenant_id(user_id, db)
    svc = SomeService(db, get_llm_client())
    result = await svc.do_thing(idea_id, tenant_id, data)
    return ResponseSchema.model_validate(result)
```

### LLM calls

All LLM calls go through `LLMService`, which renders Jinja2 prompt templates and parses structured JSON responses:

```python
# In a service
result = await self.llm_svc.score_shareability(
    component={"name": comp.name, "description": comp.description},
    idea_context=idea.title,
)
# result is a typed Pydantic model (ShareabilityScore)
```

Prompt templates live in `backend/app/llm/prompts/*.j2`. To add a new prompt:
1. Create a `.j2` template file
2. Add a typed response schema in `llm/schemas.py`
3. Add a method to `LLMService`

### Celery tasks

Tasks use a `_run()` helper to bridge sync Celery and async SQLAlchemy:

```python
def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def my_task(self, idea_id: str):
    async def _inner():
        async with async_session_factory() as db:
            # do async work
            pass
    try:
        _run(_inner())
    except Exception as exc:
        raise self.retry(exc=exc)
```

### Shareability access filtering

Use the middleware helpers before any team-facing query:

```python
from app.api.middleware.shareability import filter_ideas_by_access

query = select(Idea).where(Idea.tenant_id == tenant_id)
query = filter_ideas_by_access(query, user_id, user_tier, tenant_id, Idea.id)
ideas = list(await db.scalars(query))
```

---

## LLM Configuration

### Development (Ollama)

Ollama runs locally as a Docker service. Models are stored in the `ollama_data` volume.

```bash
# Pull all required models
make pull-models

# Check which models are available
curl http://localhost:11434/api/tags

# Test a completion
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen3:8b","messages":[{"role":"user","content":"Hello"}]}'
```

### Production (vLLM)

vLLM exposes the same OpenAI-compatible API. Swap by changing two env vars:

```bash
LLM_BACKEND=vllm
LLM_BASE_URL=http://vllm:8000/v1
```

The `docker-compose.prod.yml` does this automatically. vLLM loads the model on startup (expect 60–120s before the first request succeeds).

### Model assignment

| Task | Model variable | Why |
|------|---------------|-----|
| Planning, reasoning, Q&A, links, deps | `LLM_PLANNING_MODEL` | `qwen3:8b` — best reasoning |
| Shareability classification | `LLM_CLASSIFIER_MODEL` | `qwen3:1.7b` — fast, cheap |
| Embeddings | `LLM_EMBEDDING_MODEL` | `nomic-embed-text` — 768-dim |

---

## Adding New Features

### New API endpoint

1. Add route handler to the relevant file in `backend/app/api/v1/`
2. Add Pydantic schemas in `backend/app/schemas/`
3. Add business logic in `backend/app/services/`
4. Register the router in `backend/app/api/v1/router.py` (if new file)
5. Write tests in `backend/tests/`

### New data model

1. Create `backend/app/models/<name>.py` (inherit `Base`, `TenantMixin`, `TimestampMixin`)
2. Import it in `backend/app/models/__init__.py`
3. Import it in `backend/alembic/env.py` (so Alembic sees it)
4. Create a migration: `make revision msg="add_<name>_table"`
5. Review the generated migration — add vector columns manually if needed

### New LLM prompt

1. Create `backend/app/llm/prompts/<name>.j2`
2. Add response schema in `backend/app/llm/schemas.py`
3. Add a method to `LLMService` in `backend/app/services/llm_service.py`

### New frontend page

1. Create `frontend/src/app/<route>/page.tsx`
2. Add TypeScript types in `frontend/src/types/`
3. Add the route to `frontend/src/components/layout/Sidebar.tsx` if it's a nav item
4. Use `useSWR` + `apiFetch` for data fetching; pass `token: (session as any)?.accessToken`

---

## Production Deployment

### Using `docker-compose.prod.yml`

```bash
# Copy and fill in production .env
cp .env.example .env
# Set: JWT_SECRET, NEXTAUTH_SECRET, NEXTAUTH_URL, APP_URL, CORS_ORIGINS,
#       POSTGRES_PASSWORD, LLM_PLANNING_MODEL (vLLM model name)

# Build images
make prod-up-build

# Run migrations
make prod-migrate

# View logs
make prod-logs
```

### What changes in production

| Setting | Dev | Prod |
|---------|-----|------|
| LLM runtime | Ollama (local) | vLLM (OpenAI-compat, GPU) |
| Frontend command | `npm run dev` | `npm run start` |
| Hot-reload mounts | Yes | No |
| Restart policy | — | `always` |
| Celery Beat | Manual | Runs as separate container |
| Docs endpoint `/docs` | Exposed | Removed from Nginx |

### Nginx

The included `infra/nginx/nginx.conf` provides:
- Gzip compression for API + static assets
- Security headers (X-Frame-Options, X-Content-Type-Options, Referrer-Policy)
- Rate limiting: 10 req/s on `/api/`, 2 req/s on `/api/v1/auth/`
- WebSocket upgrade passthrough for `/api/v1/ws/`

For HTTPS, add a `server` block that listens on 443 with your TLS certificates and redirect HTTP → HTTPS.

### Scaling

- **Backend**: stateless FastAPI — add replicas behind Nginx upstream
- **Celery workers**: scale independently — `celery worker --concurrency=4`
- **Celery Beat**: run **exactly one** instance (use Redis lock or celery-redbeat for HA)
- **vLLM**: single GPU node; for multi-GPU use `--tensor-parallel-size N`

---

## CI/CD Pipeline

Three GitHub Actions workflows are included in `.github/workflows/`:

| Workflow | Trigger | What it does |
|----------|---------|-------------|
| `ci.yml` | PR to main | Ruff lint, mypy, pytest (backend); ESLint, build (frontend) |
| `docker-build.yml` | Push to main | Builds backend + frontend images, pushes to GHCR |
| `deploy.yml` | Manual dispatch | SSH to server, `docker compose pull`, `up -d`, `alembic upgrade head` |

### Required secrets (GitHub → Settings → Secrets)

| Secret | Purpose |
|--------|---------|
| `GHCR_TOKEN` | GitHub token with `packages:write` for image push |
| `DEPLOY_HOST` | Production server IP/hostname |
| `DEPLOY_USER` | SSH username on production server |
| `DEPLOY_SSH_KEY` | Private SSH key for deployment |

---

## Troubleshooting

### `make migrate` fails with "relation does not exist"

pgvector extension not enabled. Run:
```bash
docker compose exec postgres psql -U cereborate -c "CREATE EXTENSION IF NOT EXISTS vector;"
docker compose exec postgres psql -U cereborate -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
```

### Ollama model not found / LLM returns 404

```bash
make pull-models
# or manually:
docker compose exec ollama ollama pull qwen3:8b
docker compose exec ollama ollama pull qwen3:1.7b
docker compose exec ollama ollama pull nomic-embed-text
```

### Celery tasks not running

Check that the worker is up and consuming the queue:
```bash
docker compose logs celery-worker
# Should show: "celery@... ready." and task events
```

Check Redis connectivity:
```bash
docker compose exec redis redis-cli ping
# Should return: PONG
```

### JWT token rejected (401)

Ensure `JWT_SECRET` is identical between the backend and any client generating tokens. In Docker Compose it's set via `environment:` in both `backend` and `celery-worker`.

### Frontend "NEXTAUTH_URL mismatch"

`NEXTAUTH_URL` must exactly match the URL you open in the browser. If running behind a reverse proxy, set it to the public-facing URL (e.g., `https://app.example.com`).

### pgvector `<=>` operator error

Ensure the `pgvector` Python package version matches the PostgreSQL extension. Both are pinned in `pyproject.toml` and the Docker image. If you see operator errors after an upgrade, run `make down-v && make up` to recreate the volume with the latest extension.
