# Lauter

Internal recruitment workflow automation tool for Provectus. Connects Lever (ATS), Barley (interview recordings/transcripts), and Claude AI (via Amazon Bedrock) to automate candidate evaluation. Recruiters upload CVs and transcripts through a web UI; AWS Step Functions + Lambda orchestrate AI analysis and store results directly in the database.


## Architecture

```
React SPA (S3+CF) → FastAPI (ECS Fargate) → EventBridge → Step Functions → Lambdas
                         ↓                                       ↓
                    RDS Postgres                           Bedrock (Claude)
                    S3 (files)
```

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, TypeScript, Vite, TanStack Router, Tailwind v4, shadcn/ui |
| Backend | Python 3.12+, FastAPI (async), SQLModel, asyncpg, Alembic |
| Evaluation | AWS Step Functions + Lambda (5 evaluator functions) |
| AI | Claude via Amazon Bedrock |
| Auth | AWS Cognito (Google OAuth federation) + JWT |
| Infra | AWS — ECS Fargate, RDS PostgreSQL, S3, CloudFront, EventBridge |

See [`context/product/architecture.md`](context/product/architecture.md) for full architecture details.


## Prerequisites

- [Python 3.12+](https://www.python.org/)
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [Bun](https://bun.sh/) (JS runtime & package manager)
- [Docker](https://www.docker.com/) & Docker Compose
- PostgreSQL 16 (provided via Docker Compose)


## Getting Started

### 1. Clone and configure

```bash
git clone <repo-url> && cd recruitment-framework-workflow
cp app/backend/.env.example app/backend/.env
# Edit app/backend/.env with your credentials (Cognito, DB URL, JWT secret, S3)
```

### 2. Start with Docker Compose (recommended)

```bash
docker compose up -d          # Starts Postgres, MinIO, backend, and evaluator
cd app/frontend && bun install && bun run dev
```

Backend: `http://localhost:8000` | Frontend: `http://localhost:5173` | MinIO Console: `http://localhost:9101`

### 3. Or run services individually

**Database + MinIO:**
```bash
docker compose up db minio minio-init -d   # Postgres on :5437, MinIO on :9100
```

**Backend** (`app/backend/`):
```bash
uv sync                       # Install dependencies
uv run alembic upgrade head   # Apply migrations
uv run fastapi dev            # Dev server at :8000
```

**Frontend** (`app/frontend/`):
```bash
bun install                   # Install dependencies
bun run dev                   # Dev server at :5173 (proxies /api → :8000)
```

> **Note:** Docker Compose sets `DEBUG=true`, which skips Cognito and enables `POST /api/auth/dev-login` for local development. `S3_PRESIGN_ENDPOINT_URL` (`http://localhost:9100`) is separate from `S3_ENDPOINT_URL` — presigned URLs must resolve from the browser, not from inside the container.


## Project Structure

```
app/
  backend/              # FastAPI API server
    app/
      main.py           # Entrypoint, lifespan, router registration
      config.py         # pydantic-settings (reads .env)
      database.py       # Async SQLAlchemy engine + session factory
      models/           # SQLModel data models
      routers/          # API route modules
      services/         # Business logic
      schemas/          # Pydantic request/response schemas
      dependencies/     # FastAPI dependency injection
    migrations/         # Alembic (async)
    tests/              # pytest-asyncio + aiosqlite
  frontend/             # React SPA
    src/
      routes/           # TanStack file-based routes
      features/         # Domain hooks (features/{domain}/hooks/)
      widgets/          # Composite UI components
      shared/           # API client, UI components, utilities
  lambdas/              # Evaluation pipeline
    cv_analysis/        # CV parsing and requirements matching
    screening_eval/     # Screening interview evaluation
    technical_eval/     # Technical interview evaluation
    recommendation/     # Hire/no-hire recommendation
    feedback_gen/       # Candidate feedback generation
    shared/             # Common utilities (Bedrock, DB, S3)
    local_orchestrator.py  # Local Step Functions simulator
context/
  product/              # Product definition, architecture, roadmap
  spec/                 # Feature specs (per feature)
infra/                  # Terraform IaC (AWS)
docker-compose.yml      # Postgres, MinIO, backend, evaluator (dev)
```


## Commands

### Backend (`app/backend/`)

```bash
uv run fastapi dev                                       # Dev server (hot reload)
uv run pytest                                            # Run tests
uv run ruff check . && uv run ruff format .              # Lint + format
uv run alembic upgrade head                              # Apply migrations
uv run alembic revision --autogenerate -m "description"  # New migration
```

### Frontend (`app/frontend/`)

```bash
bun run dev                          # Dev server (HMR)
bun run build                        # Type-check + production build
bun run lint                         # ESLint
bun run generate:api                 # Regenerate API client from openapi.json
bunx shadcn@latest add <component>   # Add shadcn/ui component
```

### OpenAPI codegen

Re-export after changing backend routes (CI `openapi-check` will fail otherwise):

```bash
cd app/backend && uv run python scripts/export_openapi.py
cd app/frontend && bun run generate:api
```


## Configuration

All backend config is managed via environment variables loaded through pydantic-settings. Copy `.env.example` and fill in real values:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Async Postgres connection string (or use `DB_HOST`/`DB_PORT`/`DB_NAME`/`DB_USERNAME`/`DB_PASSWORD`) |
| `JWT_SECRET_KEY` | Secret for signing JWT tokens |
| `COGNITO_USER_POOL_ID` | AWS Cognito user pool ID |
| `COGNITO_CLIENT_ID` | Cognito app client ID |
| `COGNITO_CLIENT_SECRET` | Cognito app client secret |
| `COGNITO_DOMAIN` | Cognito domain for OAuth flow |
| `COGNITO_REDIRECT_URI` | OAuth callback URL |
| `S3_BUCKET_NAME` | S3 bucket for file storage |
| `S3_ENDPOINT_URL` | S3 endpoint (MinIO for local dev) |
| `S3_PRESIGN_ENDPOINT_URL` | Browser-facing S3 endpoint for presigned URLs |
| `ALLOWED_EMAIL_DOMAIN` | Restrict login to this email domain (default: `provectus.com`) |
| `DEBUG` | Enable dev-login and skip Cognito (default: `false`) |

See [`app/backend/.env.example`](app/backend/.env.example) for the full list.


## Roadmap

| Phase | Focus | Status |
|-------|-------|--------|
| 0 | AWS infra, CI/CD, evaluation pipeline architecture | Done |
| 1 | Auth, candidate/position management, CV upload, transcript upload, Barley integration | In progress |
| 2 | Screening summaries, technical evaluation, recommendation engine | Done |
| 3 | Candidate feedback generation | In progress |
| Future | Lever integration (read + write), AI candidate analyst chat | Planned |

See [`context/product/roadmap.md`](context/product/roadmap.md) for details.


## CI/CD

CI runs on PRs to `main` with path-scoped triggers. Deploy workflows use OIDC — no static AWS keys.

| Workflow | Trigger paths | Checks |
|----------|--------------|--------|
| CI Backend | `app/backend/**` | ruff, mypy, bandit, pytest, openapi-check |
| CI Frontend | `app/frontend/**` | eslint, build (includes type-check) |
| CI Lambdas | `app/lambdas/**` | ruff, pytest |
| CI Infrastructure | `infra/**` | terraform fmt/validate, version pin enforcement, tflint |
| Deploy Backend | `app/backend/**` (push to main) | Build → ECR → ECS migration task → ECS deploy |
| Deploy Frontend | `app/frontend/**` (push to main) | Build → S3 sync → CloudFront invalidation |
| Deploy Lambdas | `app/lambdas/**` (push to main) | Package → publish shared layer → update function code |


## Documentation

- [`context/product/product-definition.md`](context/product/product-definition.md) — full product definition
- [`context/product/architecture.md`](context/product/architecture.md) — system architecture
- [`context/product/roadmap.md`](context/product/roadmap.md) — product roadmap
- [`app/frontend/README.md`](app/frontend/README.md) — frontend-specific docs
- [`CLAUDE.md`](CLAUDE.md) — guidance for Claude Code
