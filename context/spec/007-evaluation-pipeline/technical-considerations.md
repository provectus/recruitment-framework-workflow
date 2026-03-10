# Technical Specification: Recruitment Interview Evaluation Pipeline

- **Functional Specification:** `context/spec/007-evaluation-pipeline/functional-spec.md`
- **Status:** Completed
- **Author(s):** Nail / Claude

---

## 1. High-Level Technical Approach

The evaluation pipeline introduces an event-driven architecture layer on top of the existing FastAPI backend. When a document upload completes, FastAPI publishes an event to EventBridge. An EventBridge rule triggers a Step Functions state machine, which orchestrates Lambda functions — one per evaluation step. Each Lambda calls Bedrock (Claude), writes results directly to RDS Postgres, and passes output to the next step. The frontend receives real-time status updates via Server-Sent Events (SSE) and fetches full results on completion.

**Systems affected:**
- **Backend (FastAPI):** New `Evaluation` model + migration, new evaluation router + service, EventBridge publishing in document_service, SSE streaming endpoint
- **Lambdas (new):** 5 Lambda functions under `app/lambdas/`, shared layer for DB access + Bedrock client
- **Infrastructure (Terraform):** EventBridge custom bus + rules, Step Functions state machine, 5 Lambda functions, IAM roles, VPC config for Lambda-to-RDS
- **Frontend:** New evaluation hooks, `EvaluationResults` widget, SSE hook for live status, toast notifications (sonner), evaluation status utilities

---

## 2. Proposed Solution & Implementation Plan (The "How")

### 2.1 Data Model / Database Changes

#### New enum: `EvaluationStepType`

| Value | Description |
|---|---|
| `cv_analysis` | CV analysis against position requirements |
| `screening_eval` | Screening transcript structured summary |
| `technical_eval` | Technical interview rubric-based evaluation |
| `recommendation` | Aggregated hire/no-hire recommendation |
| `feedback_gen` | Candidate rejection feedback draft |

#### New enum: `EvaluationStatus`

| Value | Description |
|---|---|
| `pending` | Created, waiting for Lambda to pick up |
| `running` | Lambda execution in progress |
| `completed` | Successfully finished |
| `failed` | Failed after retries exhausted |

#### New table: `evaluations`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `Integer` | PK, autoincrement | |
| `candidate_position_id` | `Integer` | FK → `candidate_positions.id`, NOT NULL, indexed | Anchor — same as documents |
| `step_type` | `String` | NOT NULL | `EvaluationStepType` value |
| `status` | `String` | NOT NULL, default `pending` | `EvaluationStatus` value |
| `version` | `Integer` | NOT NULL, default `1` | Increments on re-run; latest version displayed |
| `source_document_id` | `Integer` | FK → `documents.id`, nullable | The document that triggered this step (null for recommendation/feedback) |
| `rubric_version_id` | `Integer` | FK → `position_rubric_versions.id`, nullable | For `technical_eval` — locks the rubric version used |
| `result` | `JSON` | nullable | Step-specific structured result (JSONB) |
| `error_message` | `Text` | nullable | Failure reason if `status = failed` |
| `execution_arn` | `String` | nullable | Step Functions execution ARN for tracing |
| `started_at` | `DateTime` | nullable | When Lambda began processing |
| `completed_at` | `DateTime` | nullable | When Lambda finished |
| `created_at` | `DateTime` | server_default `now()` | |
| `updated_at` | `DateTime` | server_default `now()`, onupdate `now()` | |

**Indexes:**
- `(candidate_position_id, step_type, version)` — unique, enforces one result per step per version
- `(candidate_position_id, status)` — for SSE "any active?" queries

**Result JSONB shapes** (validated at application layer via Pydantic schemas, not at DB level — matches the rubric `structure` pattern):

- **cv_analysis:** `{ skills_match: [{skill, present, notes}], experience_relevance: str, education: str, signals_and_red_flags: str, overall_fit: str }`
- **screening_eval:** `{ key_topics: [str], strengths: [str], concerns: [str], communication_quality: str, motivation_culture_fit: str }`
- **technical_eval:** `{ criteria_scores: [{criterion_name, category_name, score, max_score, weight, evidence, reasoning}], weighted_total: float, strengths_summary: [str], improvement_areas: [str] }`
- **recommendation:** `{ recommendation: "hire"|"no_hire"|"needs_discussion", confidence: "high"|"medium"|"low", reasoning: str, missing_inputs: [str] }`
- **feedback_gen:** `{ feedback_text: str, rejection_stage: str }`

#### `candidate_positions` changes

No schema changes. The `stage` field already supports `rejected` — the HM decision gate uses the existing `update_stage` service method + the `VALID_TRANSITIONS` state machine.

---

### 2.2 Architecture Changes

#### EventBridge

- **Custom event bus:** `lauter-evaluation-events`
- **Event structure:**
  ```
  source: "lauter.api"
  detail-type: "evaluation.requested"
  detail: {
    evaluation_id: int,
    candidate_position_id: int,
    step_type: str,
    source_document_id: int | null,
    rubric_version_id: int | null
  }
  ```
- **Rule:** matches `detail-type = "evaluation.requested"`, target = Step Functions `evaluation-pipeline` state machine

#### Step Functions State Machine: `evaluation-pipeline`

The state machine receives the event detail as input. Designed as a **single-step executor** — each EventBridge event triggers one execution that runs the requested step and its downstream dependents.

```
Input → RouteByStepType (Choice)
  ├─ cv_analysis      → InvokeCvAnalysis → CheckCascade → [recommendation if technical_eval exists]
  ├─ screening_eval   → InvokeScreeningEval → CheckCascade → [recommendation if technical_eval exists]
  ├─ technical_eval   → InvokeTechnicalEval → InvokeRecommendation → End
  ├─ recommendation   → InvokeRecommendation → End
  └─ feedback_gen     → InvokeFeedbackGen → End
```

Each `Invoke*` state is a Task state calling the corresponding Lambda. Error handling: Catch on each Task with retry (2 attempts, exponential backoff), fallback to `MarkFailed` state that updates the evaluation record's status to `failed` and **continues to the next step** (fault-tolerant pipeline — a failed step does not block subsequent steps).

#### Lambda Functions

Location: `app/lambdas/`

```
app/lambdas/
  shared/             # Lambda layer: DB connection, Bedrock client, prompt utils
    db.py             # Sync SQLAlchemy engine (Lambdas use sync, not async)
    bedrock.py        # boto3 Bedrock client wrapper
    prompts/          # Prompt templates per step type
    config.py         # Reads SSM params at cold start, caches
    models.py         # Imports/re-exports relevant SQLModel models
  cv_analysis/
    handler.py        # Lambda entry point
  screening_eval/
    handler.py
  technical_eval/
    handler.py
  recommendation/
    handler.py
  feedback_gen/
    handler.py
```

**Lambda execution flow (all steps follow this pattern):**
1. Read `evaluation_id` from event input
2. Update evaluation row: `status = running`, `started_at = now()`
3. Load required data from RDS (document content from S3, position requirements, rubric, prior step results)
4. Build prompt from template + loaded data
5. Call Bedrock `InvokeModel` (Claude)
6. Parse and validate response
7. Update evaluation row: `status = completed`, `result = {...}`, `completed_at = now()`
8. Return output for Step Functions (next step input)

**Sync DB access:** Lambdas use synchronous SQLAlchemy (not async) — Lambda's single-request execution model doesn't benefit from asyncio. The shared layer provides a sync engine configured from SSM parameters.

**DB credentials:** Read from SSM Parameter Store at cold start, cached for warm invocations. Same SSM paths used by ECS task definition.

---

### 2.3 API Contracts

#### New router: `app/backend/app/routers/evaluations.py`

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/evaluations/{candidate_position_id}` | List all evaluations (latest version per step) |
| `GET` | `/api/evaluations/{candidate_position_id}/{step_type}` | Get latest evaluation for a specific step |
| `GET` | `/api/evaluations/{candidate_position_id}/{step_type}/history` | All versions of a specific step (audit trail) |
| `POST` | `/api/evaluations/{candidate_position_id}/{step_type}/rerun` | Re-run a step (creates new version, publishes EventBridge event, cascades) |
| `GET` | `/api/evaluations/{candidate_position_id}/stream` | **SSE endpoint** — streams status updates for all active evaluations |

All endpoints require `current_user: User = Depends(get_current_user)`.

#### SSE Endpoint Detail

`GET /api/evaluations/{candidate_position_id}/stream`

Returns `text/event-stream`. The server holds the connection open and polls the DB every 2-3 seconds server-side. Pushes an event whenever any evaluation's status changes.

**Event format:**
```
event: status_change
data: {"evaluation_id": 42, "step_type": "cv_analysis", "status": "running"}

event: status_change
data: {"evaluation_id": 42, "step_type": "cv_analysis", "status": "completed"}

event: done
data: {}
```

**Lifecycle:**
- Connection opens when the frontend detects any evaluation in `pending` or `running` state
- Server pushes `status_change` events as evaluations progress
- Server sends `done` event and closes the connection when all evaluations for the candidate+position are in terminal state (`completed` or `failed`)
- If no status change occurs within 30 seconds, the server sends a keepalive comment (`: keepalive`) to prevent connection timeout
- Client reconnects automatically via `EventSource` if the connection drops

**Implementation:** Use `sse-starlette` (`EventSourceResponse`) for clean async generator pattern. The handler runs an async loop: query evaluations, diff against last-sent state, yield events on change, sleep 2-3s.

#### Modified service: `document_service`

After a document upload completes (`complete_upload`, `create_pasted_transcript`):
1. Determine step type from document: `cv` → `cv_analysis`, `transcript` with `interview_stage=screening` → `screening_eval`, `transcript` with `interview_stage=technical` → `technical_eval`
2. Check if position has a rubric (required for `technical_eval`) — skip with clear message if missing
3. Create `Evaluation` row with `status=pending`
4. Publish EventBridge event via `evaluation_service.trigger_evaluation()`

#### Modified router: `candidates.py`

Extend the `update_stage` endpoint behavior:
- When stage transitions to `rejected`, call `evaluation_service.trigger_feedback_gen()` which creates a `feedback_gen` evaluation and publishes the event

#### New schemas: `app/backend/app/schemas/evaluations.py`

- `EvaluationResponse` — id, step_type, status, version, result (JSONB), error_message, started_at, completed_at, created_at
- `EvaluationListResponse` — list of `EvaluationResponse` per candidate+position
- `EvaluationHistoryResponse` — all versions of a single step
- `EvaluationStatusEvent` — lightweight SSE payload: evaluation_id, step_type, status

---

### 2.4 Frontend Component Breakdown

#### New: toast library

Install `sonner` (shadcn companion). Add `<Toaster />` to the app root layout. Use for evaluation completion/failure toast notifications triggered by SSE events.

#### New: `src/shared/lib/evaluation-utils.ts`

Evaluation status → badge variant mapping + human-readable labels for step types and statuses.

#### New hooks: `src/features/evaluations/hooks/`

| Hook | Purpose |
|---|---|
| `use-evaluations.ts` | `useQuery` — fetch all evaluations for a candidate+position |
| `use-evaluation-history.ts` | `useQuery` — fetch version history for a specific step |
| `use-rerun-evaluation.ts` | `useMutation` — POST to rerun endpoint, invalidates evaluation queries |
| `use-evaluation-stream.ts` | **SSE hook** — connects to `/stream` endpoint, fires toast notifications, invalidates evaluation queries on `status_change` events |

**SSE hook detail (`use-evaluation-stream.ts`):**
- Opens `EventSource` connection when any evaluation is `pending` or `running`
- On `status_change` event: show toast (success or error), invalidate `use-evaluations` query to refetch full results
- On `done` event: close connection
- Auto-reconnects on connection drop (native `EventSource` behavior)
- Closes connection on component unmount or when no evaluations are active

**Why SSE + query invalidation (not SSE + full payload):** SSE sends lightweight status-only events. On each `status_change` to `completed`, the hook invalidates the `use-evaluations` query, which triggers a standard GET to fetch the full result. This keeps SSE payloads small and reuses the existing query cache.

#### New widgets: `src/widgets/evaluations/`

| Widget | Description |
|---|---|
| `evaluation-results.tsx` | Container: renders a card per step with status badge, results, re-run button. Mounted on candidate detail page. Manages SSE connection via `use-evaluation-stream`. |
| `evaluation-step-card.tsx` | Single step card: status badge, timestamp, structured result content, error message (if failed), re-run button |
| `cv-analysis-result.tsx` | Renders CV analysis JSONB: skills match table, experience narrative, signals/red flags |
| `screening-eval-result.tsx` | Renders screening summary: 5 labeled sections with bullet lists |
| `technical-eval-result.tsx` | Renders rubric scores: criterion table with score bars, weighted total, strengths/improvements |
| `recommendation-result.tsx` | Renders recommendation: hire/no-hire badge, confidence level, reasoning, missing data callout |
| `feedback-draft-result.tsx` | Renders feedback text with edit capability (textarea) for HM review |
| `hm-decision-gate.tsx` | Proceed/Reject buttons with optional notes textarea, triggers stage transition |

#### Modified: candidate detail page

Add `EvaluationResults` widget between the positions table and documents section. Pass `candidatePositionId` (selected via the positions table or a new position selector if the candidate has multiple positions).

---

### 2.5 Infrastructure (Terraform)

New resources under `infra/`:

| Resource | Description |
|---|---|
| `aws_cloudwatch_event_bus` | Custom bus `lauter-evaluation-events` |
| `aws_cloudwatch_event_rule` | Matches `evaluation.requested` events |
| `aws_cloudwatch_event_target` | Routes to Step Functions |
| `aws_sfn_state_machine` | `evaluation-pipeline` standard workflow |
| `aws_lambda_function` × 5 | One per evaluation step (Python 3.12, 512MB, 5min timeout) |
| `aws_lambda_layer_version` | Shared Python layer (DB, Bedrock, prompts) |
| `aws_iam_role` per Lambda | Bedrock InvokeModel, S3 GetObject, RDS connect, CloudWatch Logs, SSM GetParameter |
| `aws_iam_role` for Step Functions | Lambda invoke, CloudWatch Logs |
| `aws_iam_role` for EventBridge | Step Functions StartExecution |
| `aws_security_group` | Lambda SG — outbound to RDS SG, Bedrock endpoint |
| SSM parameters | DB connection details (if not already provisioned) |

Lambdas are VPC-attached (same VPC as ECS/RDS) and need NAT Gateway for Bedrock access (public endpoint).

New env var for backend ECS task definition: `EVALUATION_EVENT_BUS_NAME`.

New backend dependency: `sse-starlette` (for SSE endpoint), `boto3` (for EventBridge PutEvents — may already be available via existing S3 dependency).

---

## 3. Impact and Risk Analysis

### System Dependencies

| Dependency | Impact |
|---|---|
| Document upload flow | Modified — triggers evaluation after `complete_upload` / `create_pasted_transcript` |
| Candidate stage transitions | Modified — `rejected` stage triggers `feedback_gen` |
| Position rubric system | Read-only — `technical_eval` reads current rubric version |
| S3 file storage | Read-only — Lambdas read CV/transcript content |
| Bedrock (Claude) | New dependency — all Lambdas call InvokeModel |

### Potential Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| **Bedrock latency/timeout** | Evaluations stall or fail | 5-min Lambda timeout; Step Functions retry 2×; fault-tolerant pipeline continues past failed steps |
| **Lambda cold starts** | Slow first evaluation | Monitor p99 latency; add provisioned concurrency if needed post-deploy |
| **VPC NAT Gateway cost** | Lambda in VPC requires NAT for Bedrock | Consider VPC endpoint for Bedrock if available; monitor NAT data transfer costs |
| **Large transcripts exceed token limits** | Bedrock rejects request | Implement transcript chunking/truncation in Lambda with warning in result |
| **Prompt quality** | Poor evaluation output | Version-control prompts in `app/lambdas/shared/prompts/`; iterate with sample transcripts before production |
| **RDS connection exhaustion** | Multiple concurrent Lambdas overwhelm DB | Use RDS Proxy or limit Lambda concurrency (reserved concurrency = 10 per function) |
| **EventBridge event loss** | Evaluation never starts | EventBridge built-in retry + DLQ; add CloudWatch alarm on DLQ depth |
| **SSE connection limits** | Too many open connections on ECS | One SSE connection per candidate page view; ECS scales horizontally; ALB distributes |
| **SSE through CloudFront** | CloudFront may buffer SSE responses | API calls go to ALB directly (not CloudFront); verify CORS allows SSE from SPA origin |

---

## 4. Testing Strategy

### Backend (FastAPI)

- **Unit tests:** evaluation_service functions — create, trigger, re-run, status transitions. Mock EventBridge client (boto3).
- **Integration tests:** full flow from document upload → evaluation record creation. Uses existing test infrastructure (aiosqlite in-memory). EventBridge publishing mocked at boto3 level.
- **API tests:** evaluation router endpoints — list, get, history, rerun. Standard httpx AsyncClient pattern.
- **SSE tests:** verify `/stream` endpoint returns `text/event-stream` content type, emits `status_change` events when evaluation status updates, sends `done` when all terminal. Use httpx streaming response.

### Lambdas

- **Unit tests per Lambda:** mock Bedrock responses + DB session, verify correct result JSONB structure written to DB. Use pytest (sync).
- **Integration tests:** run Lambda handler locally with test DB, mock Bedrock responses. Verify end-to-end data flow.
- **Prompt tests:** sample transcripts → expected output structure validation (not content correctness — that's qualitative).

### Frontend

- **Component tests:** render evaluation widgets with mock data, verify correct display of scores/summaries/status badges.
- **Hook tests:** verify SSE hook connects when evaluations are active, fires query invalidation on `status_change`, disconnects on `done` or unmount.

### E2E (manual for POC)

- Upload CV → verify cv-analysis evaluation appears with results in real-time (SSE)
- Upload screening transcript → verify screening-eval appears
- Upload technical transcript → verify technical-eval + recommendation cascade
- Reject candidate → verify feedback-gen triggers
- Re-run a step → verify new version created and downstream cascade
- Close browser tab during evaluation → reopen → verify results display correctly (GET endpoint)
