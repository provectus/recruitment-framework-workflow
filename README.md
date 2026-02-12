# Tap

Internal recruitment workflow automation tool for Provectus. Connects Lever (ATS), Barley (interview recordings/transcripts), and Claude AI (via Amazon Bedrock) to automate candidate evaluation. Recruiters upload CVs and transcripts through a web UI; n8n workflows orchestrate AI analysis and push results back to Lever.


## Architecture

```
React SPA (S3+CF) → FastAPI (ECS Fargate) ↔ n8n (on-prem Docker)
                         ↓                        ↓
                    RDS Postgres              Bedrock (Claude)
                    S3 (files)               Lever API
```

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, TypeScript, Vite, TanStack Router, Tailwind v4, shadcn/ui |
| Backend | Python 3.12+, FastAPI (async), SQLModel, asyncpg, Alembic |
| Workflow | n8n (self-hosted, Docker Compose) |
| AI | Claude via Amazon Bedrock |
| Auth | Google OAuth 2.0 (corporate Workspace) |
| Infra | AWS — ECS Fargate, RDS PostgreSQL, S3, CloudFront |

See [`context/product/architecture.md`](context/product/architecture.md) for full architecture details.


## Prerequisites

- [Python 3.12+](https://www.python.org/)
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [Bun](https://bun.sh/) (JS runtime & package manager)
- [Docker](https://www.docker.com/) & Docker Compose
- PostgreSQL 16 (provided via Docker Compose, or install locally)


## Getting Started

### 1. Clone and configure

```bash
git clone <repo-url> && cd recruitment-framework
cp app/backend/.env.example app/backend/.env
# Edit app/backend/.env with your credentials (Google OAuth, DB URL, JWT secret)
```

### 2. Start with Docker Compose (recommended)

```bash
docker compose up -d          # Starts Postgres + backend
cd app/frontend && bun install && bun run dev
```

Backend: `http://localhost:8000` | Frontend: `http://localhost:5173`

### 3. Or run services individually

**Database:**
```bash
docker compose up db -d       # Postgres on port 5437
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
    migrations/         # Alembic (async)
    tests/              # pytest-asyncio + aiosqlite
  frontend/             # React SPA
    src/
      routes/           # TanStack file-based routes
      components/ui/    # shadcn/ui components
      lib/              # Auth, utilities
context/
  product/              # Product definition, architecture, roadmap
  spec/                 # Feature specs (per feature)
docker-compose.yml      # Postgres + backend (dev)
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
bunx shadcn@latest add <component>   # Add shadcn/ui component
```


## Configuration

All backend config is managed via environment variables loaded through pydantic-settings. Copy `.env.example` and fill in real values:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Async Postgres connection string |
| `JWT_SECRET_KEY` | Secret for signing JWT tokens |
| `COGNITO_CLIENT_ID` | Google OAuth client ID (via Cognito) |
| `COGNITO_CLIENT_SECRET` | Google OAuth client secret |
| `COGNITO_DOMAIN` | Cognito domain for OAuth flow |
| `ALLOWED_EMAIL_DOMAIN` | Restrict login to this email domain (e.g. `provectus.com`) |

See [`app/backend/.env.example`](app/backend/.env.example) for the full list.


## Roadmap

| Phase | Focus | Status |
|-------|-------|--------|
| 0 | AWS infra, n8n instance, CI/CD | Planned |
| 1 | Auth, candidate list, CV upload, Lever + Barley integrations | In progress |
| 2 | Screening summaries, technical evaluation, recommendation engine | Planned |
| 3 | Lever write-back, candidate feedback generation | Planned |

See [`context/product/roadmap.md`](context/product/roadmap.md) for details.


## Documentation

- [`context/product/product-definition.md`](context/product/product-definition.md) — full product definition
- [`context/product/architecture.md`](context/product/architecture.md) — system architecture
- [`context/product/roadmap.md`](context/product/roadmap.md) — product roadmap
- [`app/frontend/README.md`](app/frontend/README.md) — frontend-specific docs
- [`CLAUDE.md`](CLAUDE.md) — guidance for Claude Code
