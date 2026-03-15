# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Lauter** — an internal recruitment workflow automation tool for Provectus. Connects Lever (ATS), Barley (interview recordings/transcripts), and Claude AI (via Amazon Bedrock) to automate candidate evaluation. Recruiters upload CVs/transcripts through a web UI; AWS Step Functions + Lambda orchestrate AI evaluation pipeline and write results directly to the database.

See `context/product/` for product definition, architecture, roadmap, and POC plans.

## Architecture

```
React SPA (S3+CF) → FastAPI (ECS Fargate) → EventBridge → Step Functions → Lambdas
                         ↓                                       ↓
                    RDS Postgres                           Bedrock (Claude)
                    S3 (files)
```

- **Frontend:** React 19 + TypeScript SPA, Vite, TanStack Router (file-based routing with auto code-splitting), Tailwind v4, shadcn/ui (new-york style, Lucide icons), React Compiler enabled
- **Backend:** Python 3.12+, FastAPI (async), SQLModel + asyncpg (Postgres), Alembic (async migrations), pydantic-settings for config
- **Evaluation pipeline:** EventBridge (custom bus) → Step Functions (standard workflow) → 5 Lambda functions (Python 3.12, VPC-attached, write to RDS directly)
- **Auth:** AWS Cognito (Google OAuth federation) + JWT (dev login)

## Local Development

Use `/setup` skill to guide new engineers through full environment setup.

Quick start: `docker compose up -d` then `cd app/frontend && bun install && bun run dev`

**Key ports:** Backend :8000, Frontend :5173, Postgres :5437, MinIO :9100 (console :9101)

Docker Compose overrides backend env vars (`DEBUG=true`, `DATABASE_URL`, S3 endpoints). `S3_PRESIGN_ENDPOINT_URL` (`http://localhost:9100`) is separate from `S3_ENDPOINT_URL` — presigned URLs must resolve from the browser, not from inside the container.

OpenAPI codegen: re-export after changing routes or CI `openapi-check` will fail.

```bash
cd app/backend && uv run python scripts/export_openapi.py
cd app/frontend && bun run generate:api
```

## Conventions

- When creating shell scripts or entrypoint files, always set execute permissions (`chmod +x`) immediately after creating them
- Backend, frontend, and infrastructure conventions are in `.claude/rules/` — auto-loaded by glob when editing files in those directories

## CI/CD

Deploy jobs in `.github/workflows/` use OIDC (`role-to-assume`) — no static AWS keys. CI runs on PRs to `main` (backend: ruff/mypy/bandit/pytest/openapi-check, frontend: eslint/build, lambdas: ruff/pytest, infra: fmt/validate/tflint). Lambda deploy packages each function as a zip, publishes a shared layer with dependencies + `shared/` code, then updates all 5 function configurations.
