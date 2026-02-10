# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Barley** — an internal recruitment workflow automation tool for Provectus. Connects Lever (ATS), Barley (interview recordings/transcripts), and Claude AI (via Amazon Bedrock) to automate candidate evaluation. Recruiters upload CVs/transcripts through a web UI; n8n workflows orchestrate AI analysis and push results back to Lever.

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
app/
  backend/          # FastAPI app (managed with uv)
    app/
      main.py       # FastAPI entrypoint, lifespan, router registration
      config.py     # pydantic-settings (reads .env)
      database.py   # async SQLAlchemy engine + session factory
      models/       # SQLModel models (imported by Alembic env.py)
      routers/      # FastAPI route modules
      services/     # Business logic layer
    migrations/     # Alembic (async, renders as batch, SQLModel metadata)
    tests/          # pytest-asyncio, aiosqlite in-memory, httpx AsyncClient
  frontend/         # React SPA (managed with bun)
    src/
      routes/       # TanStack file-based routes (auto-generates routeTree.gen.ts)
      components/ui # shadcn/ui components
      lib/          # Utility functions
context/
  product/          # Product definition, architecture, roadmap, POC plans
  spec/             # Functional and technical specs (per feature)
```

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
```

### Frontend (`app/frontend/`)

```bash
bun install                             # Install deps
bun run dev                             # Dev server (Vite)
bun run build                           # Type-check + production build
bun run lint                            # ESLint
bun run preview                         # Preview production build
bunx shadcn@latest add <component>      # Add shadcn/ui component
```

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
