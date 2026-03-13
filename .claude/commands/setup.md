---
name: setup
description: Set up local development environment for new engineers. Checks prerequisites, starts services, verifies everything works.
---

# Local Environment Setup

Guide the engineer through setting up the Lauter development environment. Run each step, verify it works, and troubleshoot if needed.

## Prerequisites Check

Check that these tools are installed. For each missing one, tell the user how to install it (Homebrew on macOS):

1. **Docker** — `docker --version` (need Docker Desktop running)
2. **bun** — `bun --version`
3. **uv** — `uv --version`
4. **Python 3.12+** — `python3 --version`

If any are missing, list them all at once and wait for the user to install before continuing.

## Step 1: Backend .env

Check if `app/backend/.env` exists.
- If not: copy from `.env.example`, then set these values for local Docker dev:
  - `DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/lauter`
  - `DEBUG=false` (Docker Compose overrides to `true`)
  - `COOKIE_SECURE=false`
  - `S3_ENDPOINT_URL=http://minio:9000`
  - `S3_PRESIGN_ENDPOINT_URL=http://localhost:9100`
- If exists: verify `COOKIE_SECURE=false` is set (common gotcha for local dev)

## Step 2: Start Docker Services

```bash
docker compose up -d
```

Wait for healthy status on all services. Verify:
- **Postgres:** `docker compose exec db pg_isready -U postgres`
- **MinIO:** `curl -s http://localhost:9100/minio/health/live`
- **Backend:** `curl -s http://localhost:8000/api/health`

If backend fails to start, check logs: `docker compose logs backend --tail 50`

Common issues:
- Port 5437 in use → another Postgres running. Stop it or change the port in `docker-compose.yml`
- Port 8000 in use → another service on that port
- Backend can't connect to DB → `.env` has `localhost` instead of `db` for DB_HOST (Docker networking)
- Presigned URLs don't work in browser → `S3_PRESIGN_ENDPOINT_URL` must be `http://localhost:9100` (browser-accessible), not the internal Docker URL

## Step 3: Frontend

```bash
cd app/frontend && bun install && bun run dev
```

Verify: `curl -s http://localhost:5173` returns HTML.

## Step 4: Seed Dev Data

```bash
cd app/backend && docker compose exec backend python -m scripts.seed
```

This creates sample users, teams, positions, and candidates for local testing.

## Step 5: Verify Login

Tell the user to open http://localhost:5173 in their browser. Since `DEBUG=true` (set by Docker Compose), the dev-login page should be available — no Cognito needed locally.

## Step 6: OpenAPI Client (optional)

If the engineer will work on frontend, regenerate the API client:

```bash
cd app/backend && uv run python scripts/export_openapi.py
cd app/frontend && bun run generate:api
```

## Done

Summarize what's running:
- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000 (docs at /docs)
- **MinIO Console:** http://localhost:9101 (minioadmin/minioadmin)
- **Postgres:** localhost:5437, db=lauter, user=postgres/postgres

Mention: `docker compose down` to stop, `docker compose down -v` to also wipe data volumes.
