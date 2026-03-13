# Local Evaluation Pipeline

## Problem

Locally, the backend creates `Evaluation` records and publishes to EventBridge, but nothing processes them — evaluations stay `pending` forever. No Lambda, Step Functions, or EventBridge run locally. We need end-to-end pipeline testing without AWS dependencies.

## Solution

Two components: a **mock Bedrock layer** for offline LLM simulation and a **local orchestrator** that replaces EventBridge + Step Functions + Lambda locally.

## Component 1: Mock Bedrock

Intercept at `shared/bedrock.py`. When `MOCK_BEDROCK=true`, `invoke_claude()` returns hardcoded JSON instead of calling AWS.

### New file: `app/lambdas/shared/mock_bedrock.py`
- Dict mapping step type → canned JSON response string (5 responses, one per step type)
- Adds configurable delay (`MOCK_BEDROCK_DELAY_SECONDS`, default 3s) to simulate processing time
- Step type passed via optional `step_type` kwarg on `invoke_claude()`

### Failure simulation
- `MOCK_EVALUATION_FAILURES` env var — comma-separated step types that should fail (e.g. `technical_eval,screening_eval`)
- Steps in the failure list raise `RuntimeError("Mock Bedrock failure for {step_type}")` after the delay
- Handler's existing `except` block catches it → `status=failed` + `error_message` — identical to real Bedrock failure path
- Default: empty string (all succeed)

## Component 2: Local Orchestrator

Standalone Python script (`app/lambdas/local_orchestrator.py`) running as a docker-compose service.

### Behavior
1. Polls `evaluations` table every 2s for `status = 'pending'`
2. Builds EventBridge-format event dict: `{"detail": {"evaluation_id": <id>, "candidate_position_id": <id>, "step_type": "<type>"}}`
3. Imports and calls the correct handler (e.g. `cv_analysis.handler.handler(event, None)`)
4. Handlers do all real work — DB updates, S3 reads, mock Bedrock calls
5. If handler raises, logs error and moves on (handler already set `status=failed`)
6. Sequential processing — one evaluation at a time

### Docker-compose service
```yaml
evaluator:
  build:
    context: ./app/lambdas
    dockerfile: Dockerfile.local
  depends_on:
    db: { condition: service_healthy }
    minio: { condition: service_healthy }
  environment:
    DB_HOST: db
    DB_PORT: 5432
    DB_NAME: lauter
    DB_USERNAME: postgres
    DB_PASSWORD: postgres
    S3_ENDPOINT_URL: http://minio:9000
    S3_BUCKET_NAME: lauter-files
    MOCK_BEDROCK: "true"
    MOCK_BEDROCK_DELAY_SECONDS: "3"
    MOCK_EVALUATION_FAILURES: ""
    AWS_ACCESS_KEY_ID: minioadmin
    AWS_SECRET_ACCESS_KEY: minioadmin
```

### Dockerfile.local
Minimal Python 3.12 image. Installs lambda deps (psycopg2, sqlalchemy, boto3, pypdf, python-docx). Copies `app/lambdas/` code. Runs `python local_orchestrator.py`.

## Changes to Existing Code

Three existing files modified (minimal):

1. **`shared/bedrock.py`** — Mock check at top of `invoke_claude()`. If `MOCK_BEDROCK` truthy, delegate to `mock_bedrock.py`.
2. **`shared/s3.py`** — Add `S3_ENDPOINT_URL` support to `get_client()` for MinIO.
3. **`shared/config.py`** — Add `MOCK_BEDROCK`, `MOCK_BEDROCK_DELAY_SECONDS`, `MOCK_EVALUATION_FAILURES`, `S3_ENDPOINT_URL` env var reads.

No backend, frontend, or infra changes. Backend already skips EventBridge when bus name is empty — evaluations created as `pending`, orchestrator picks them up.

## New Files Summary

| File | Purpose |
|------|---------|
| `app/lambdas/shared/mock_bedrock.py` | Canned responses + failure simulation |
| `app/lambdas/local_orchestrator.py` | Poll DB + dispatch to handlers |
| `app/lambdas/Dockerfile.local` | Container for orchestrator service |
| `docker-compose.yml` (modified) | Add `evaluator` service |

## End-to-End Local Flow

```
Upload CV → Backend creates Evaluation (pending) → Orchestrator polls DB →
  picks up pending → calls handler → handler reads S3 (MinIO) →
  calls Bedrock (mocked) → writes result to DB → SSE streams to frontend
```
