# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Tech Stack

- **Frontend:** TypeScript, React 19, TanStack Query, TanStack Router, shadcn/ui, Tailwind v4, hey-api for API codegen, Feature-Sliced Design (FSD) architecture
- **Backend:** Python 3.12+, FastAPI, SQLModel, Alembic migrations, PostgreSQL, asyncpg
- **Infrastructure:** Docker Compose for local dev, Terraform for cloud (AWS), MinIO for local S3

## Debugging & Bug Fixes

When fixing bugs, always verify the fix actually resolves the issue before committing. If the first fix attempt fails, step back and investigate the root cause more deeply rather than applying incremental patches.

## Workflow Rules

- Always run `bun run build` AND `bun run lint` after making frontend changes before considering a task complete
- For backend changes, run the test suite (`uv run pytest`) before considering complete
- Never commit without verifying the build passes locally

## Code Review Guidelines

When reviewing code or flagging issues, do NOT flag standard library/framework patterns as bugs. Specifically: `'use client'` directives in shadcn components are expected defaults, not issues. Apply a reasonable confidence threshold — only report issues you are 85%+ confident are real problems.

## Project Overview

**Tap** — an internal recruitment workflow automation tool for Provectus. Connects Lever (ATS), Barley (interview recordings/transcripts), and Claude AI (via Amazon Bedrock) to automate candidate evaluation. Recruiters upload CVs/transcripts through a web UI; n8n workflows orchestrate AI analysis and push results back to Lever.

See `context/product/` for product definition, architecture, roadmap, and POC plans.

## Architecture

```
React SPA (S3+CF) → FastAPI (ECS Fargate) ↔ n8n (on-prem Docker)
                         ↓                        ↓
                    RDS Postgres              Bedrock (Claude)
                    S3 (files)               Lever API
```

- **Frontend:** React 19 + TypeScript SPA, Vite, TanStack Router (file-based routing with auto code-splitting), Tailwind v4, shadcn/ui (new-york style, Lucide icons), React Compiler enabled
- **Backend:** Python 3.12+, FastAPI (async), SQLModel + asyncpg (Postgres), Alembic (async migrations), pydantic-settings for config
- **Workflow engine:** n8n self-hosted on-prem, triggered via webhooks from FastAPI
- **Auth:** Google OAuth 2.0 (corporate Workspace)

## Repository Structure

```
docker-compose.yml  # Local dev: Postgres 16, MinIO (S3), backend w/ hot reload
app/
  backend/          # FastAPI app (managed with uv)
    app/
      main.py       # Entrypoint, lifespan, router registration
      config.py     # pydantic-settings (reads .env)
      database.py   # async SQLAlchemy engine + session factory
      models/       # SQLModel models (candidate, position, document, team, user, enums)
      routers/      # FastAPI route modules (auth, candidates, documents, positions, teams, users, health)
      services/     # Business logic layer (auth, candidate, document, position, storage, team, user)
    migrations/     # Alembic (async, renders as batch, SQLModel metadata)
    scripts/        # seed.py (dev data), export_openapi.py (generates frontend/openapi.json)
    tests/          # pytest-asyncio, aiosqlite in-memory, httpx AsyncClient
    Dockerfile      # Multi-stage: base → dev (hot reload) / prod
    entrypoint.sh   # Runs alembic upgrade head before app start
  frontend/         # React SPA (managed with bun)
    openapi.json    # Generated OpenAPI spec — source for API client codegen
    src/
      routes/       # TanStack file-based routes (routeTree.gen.ts auto-generated)
      features/     # Feature modules (auth, candidates, documents, positions, settings)
      widgets/      # Composite UI blocks (candidates, dashboard, documents, positions, sidebar)
      shared/       # api/ (generated client), lib/, ui/ (shadcn components)
infra/              # Terraform IaC — VPC, ECS, RDS, S3, CloudFront, Cognito, IAM, ACM, monitoring
.github/workflows/  # CI + deploy pipelines (see CI/CD section)
context/
  product/          # Product definition, architecture, roadmap, POC plans
  spec/             # Functional and technical specs (per feature)
```

## Local Development

### Full stack via Docker Compose
```bash
# Start Postgres + MinIO + backend (auto-runs migrations)
docker compose up -d
# Frontend runs outside Docker
cd app/frontend && bun install && bun run dev
```
- **Postgres:** port 5437, db `tap`, user/pass `postgres/postgres`
- **MinIO (S3):** API port 9100, console port 9101, user/pass `minioadmin/minioadmin`, bucket `tap-files`
- **Backend:** port 8000, hot-reload, reads `app/backend/.env`
- **Frontend:** port 5173 (Vite default)

The database runs via Docker Compose on localhost (not the Docker service name). The `.env` should use `localhost` for `DB_HOST` when running the app outside Docker. Always check `.env` configuration when debugging connection issues.

### Backend standalone (without Docker)
```bash
cd app/backend
cp .env.example .env                    # Edit DATABASE_URL to point at your Postgres
uv run alembic upgrade head             # Apply migrations
uv run fastapi dev                      # Start dev server on :8000
```

### Seed dev data
```bash
cd app/backend && uv run python -m scripts.seed
```

### OpenAPI → Frontend client codegen
```bash
cd app/backend && uv run python scripts/export_openapi.py   # Writes app/frontend/openapi.json
cd app/frontend && bun run generate:api                      # Regenerates src/shared/api/
```
The CI `openapi-check` job fails if openapi.json is stale — always re-export after changing routes.

## Commands

### Backend (`app/backend/`)

```bash
uv run fastapi dev                      # Dev server with hot reload
uv run pytest                           # Run all tests
uv run pytest tests/test_health.py      # Run single test file
uv run pytest -k test_health_check      # Run single test by name
uv run ruff check .                     # Lint
uv run ruff format .                    # Format
uv run alembic upgrade head             # Apply migrations
uv run alembic revision --autogenerate -m "description"  # Create migration
uv run mypy app/                        # Type check
uv run bandit -r app/ -c pyproject.toml # Security scan
uv run python -m scripts.seed           # Seed local DB with dev data
uv run python scripts/export_openapi.py # Regenerate frontend/openapi.json
```

### Frontend (`app/frontend/`)

```bash
bun install                             # Install deps
bun run dev                             # Dev server (Vite)
bun run build                           # Type-check + production build
bun run lint                            # ESLint
bun run preview                         # Preview production build
bunx shadcn@latest add <component>      # Add shadcn/ui component
bun run generate:api                    # Regenerate API client from openapi.json
```

## Conventions

- When creating shell scripts or entrypoint files, always set execute permissions (`chmod +x`) immediately after creating them

## Key Conventions

### Backend
- **Async everywhere:** all DB operations, routes, and tests use async/await
- **Config via `.env`:** pydantic-settings `Settings` class in `config.py` — all env vars go through this
- **Tests use SQLite:** `conftest.py` overrides the DB session with aiosqlite; uses `setup_database` autouse fixture for create/drop per test
- **Ruff rules:** `F E W I UP B C4 SIM FA ISC ICN RET TC PTH RUF` — line length 88, Python 3.12 target
- **Alembic:** async engine, `render_as_batch=True`, file template `YYYY-MM-DD_slug`, models must be imported in `models/__init__.py` for autogenerate to detect them
- **Router pattern:** each module in `routers/` creates an `APIRouter`, registered in `main.py` via `app.include_router()`

### Frontend
- **Path alias:** `@/` maps to `src/` (configured in vite.config.ts and tsconfig)
- **Routing:** file-based via TanStack Router — add routes as files under `src/routes/`, `routeTree.gen.ts` is auto-generated (do not edit manually)
- **UI components:** shadcn/ui with `components.json` config (rsc: false, baseColor: slate, cssVariables: true)
- **Package manager:** bun (not npm/yarn)
- **API client:** auto-generated via `@hey-api/openapi-ts` from `openapi.json` → `src/shared/api/`. Do not edit `shared/api/` manually.
- **Layout:** features/ (domain logic), widgets/ (composite UI), shared/ (api, lib, ui components)
- **Data fetching:** TanStack React Query with generated query/mutation options from the API client
- **Forms:** react-hook-form + zod validation

## CI/CD Workflows (`.github/workflows/`)

| Workflow | Trigger | What it does |
|---|---|---|
| `ci-backend.yml` | PR → `main` (backend paths) | ruff lint + format check, mypy, bandit security scan, pytest, OpenAPI spec freshness |
| `ci-frontend.yml` | PR → `main` (frontend paths) | bun install, generate API client, eslint, build (includes tsc) |
| `dependency-review.yml` | PR → `main` | Flags high-severity dependency vulnerabilities |
| `deploy-backend.yml` | Push to `main` (backend paths) | Lint/test → Docker build → push to ECR → ECS force-new-deployment |
| `deploy-frontend.yml` | Push to `main` (frontend paths) | Lint/build → S3 sync → CloudFront invalidation |

Deploy jobs use OIDC (`role-to-assume`) — no static AWS keys in secrets.

## Development Workflow

### Feature lifecycle (AWOS skills in `.awos/`)
Each feature follows: **roadmap → spec → tech → tasks → implement → verify**
1. Roadmap item checked in `context/product/roadmap.md`
2. Functional spec: `context/spec/NNN-name/functional-spec.md` — what & why, testable acceptance criteria
3. Technical spec: `context/spec/NNN-name/technical-considerations.md` — data model, API design, implementation approach
4. Task list: `context/spec/NNN-name/tasks.md` — vertical slices, each keeping the app runnable
5. Implementation via subagent delegation per task slice
6. Verification against acceptance criteria

### Feature build order
Backend first (model → service → router → tests), then frontend (features → widgets → routes).
After feature completion: code review pass, then CI fix pass.

### Commit conventions
Emoji prefix + conventional commit: `✨ feat:`, `🐛 fix:`, `📝 docs:`, `🔧 chore:`, `♻️ refactor:`, `🚀 ci:`, `🏗️ feat:` (infra), `🔒️ fix:` (security), `💚 fix:` (CI)

### Spec numbering
Sequential in `context/spec/`: 001-authentication, 002-infrastructure, 003-lever-api-research, 004-core-data-management, 005-document-uploads. Next spec gets `006-*`.

