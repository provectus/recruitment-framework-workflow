# Tasks: Recruitment Interview Evaluation Pipeline

- **Specification:** `context/spec/007-evaluation-pipeline/`
- **Status:** Draft

---

## Slice 1: Evaluation data model + list API

> Foundation: new model, migration, CRUD endpoints. No AI, no events. App runnable — evaluations can be created and read via API.

- [x] **Slice 1: Evaluation data model and basic CRUD API**
  - [x] Add `EvaluationStepType` enum (`cv_analysis`, `screening_eval`, `technical_eval`, `recommendation`, `feedback_gen`) and `EvaluationStatus` enum (`pending`, `running`, `completed`, `failed`) to `app/backend/app/models/enums.py` **[Agent: python-architect]**
  - [x] Create `Evaluation` SQLModel in `app/backend/app/models/evaluation.py` with all columns from tech spec: `id`, `candidate_position_id` (FK), `step_type`, `status`, `version`, `source_document_id` (FK), `rubric_version_id` (FK), `result` (JSON), `error_message`, `execution_arn`, `started_at`, `completed_at`, `created_at`, `updated_at`. Add composite unique index on `(candidate_position_id, step_type, version)` and index on `(candidate_position_id, status)` **[Agent: python-architect]**
  - [x] Register the new model in `app/backend/app/models/__init__.py` **[Agent: python-architect]**
  - [x] Generate Alembic migration: `uv run alembic revision --autogenerate -m "add evaluations table"` and verify the generated migration **[Agent: python-architect]**
  - [x] Create Pydantic schemas in `app/backend/app/schemas/evaluations.py`: `EvaluationResponse`, `EvaluationListResponse`, `EvaluationHistoryResponse`, `EvaluationStatusEvent` (SSE payload) **[Agent: python-architect]**
  - [x] Create `app/backend/app/services/evaluation_service.py` with async functions: `get_evaluations(session, candidate_position_id)` → returns latest version per step; `get_evaluation_by_step(session, candidate_position_id, step_type)` → latest version of a specific step; `get_evaluation_history(session, candidate_position_id, step_type)` → all versions ordered by version desc; `create_evaluation(session, candidate_position_id, step_type, source_document_id, rubric_version_id)` → creates row with status=pending **[Agent: python-architect]**
  - [x] Create `app/backend/app/routers/evaluations.py` with endpoints: `GET /api/evaluations/{candidate_position_id}` (list latest per step), `GET /api/evaluations/{candidate_position_id}/{step_type}` (latest for step), `GET /api/evaluations/{candidate_position_id}/{step_type}/history` (all versions). All require `current_user` auth dependency. Register router in `main.py` **[Agent: python-architect]**
  - [x] Write tests: model creation, service CRUD functions, router endpoints (list, get, history). Follow existing test patterns (aiosqlite, httpx AsyncClient) **[Agent: typescript-test-expert]**
  - [x] Run `uv run pytest`, `uv run ruff check .`, `uv run ruff format .`, `uv run mypy app/` — verify all pass **[Agent: python-architect]**
  - [x] Regenerate OpenAPI spec: `uv run python scripts/export_openapi.py` and regenerate frontend client: `cd app/frontend && bun run generate:api` **[Agent: python-architect]**
  - [x] **Verify:** Start the app (`docker compose up -d`), call `GET /api/evaluations/1` via curl — should return empty list (200). Call `GET /api/evaluations/999` — should return empty list or 404 if candidate_position doesn't exist. **[Agent: general-purpose]**

---

## Slice 2: EventBridge integration + auto-trigger on document upload

> Wire document upload → evaluation creation → EventBridge event. Uploading a CV/transcript now creates a pending evaluation and publishes an event. Nothing consumes it yet.

- [x] **Slice 2: Trigger evaluation on document upload via EventBridge**
  - [x] Add `EVALUATION_EVENT_BUS_NAME` to `app/backend/app/config.py` Settings class (string, default empty — EventBridge disabled when empty for local dev) **[Agent: python-architect]**
  - [x] Add `boto3` as backend dependency if not already present (`uv add boto3`) **[Agent: python-architect]**
  - [x] Create `app/backend/app/services/eventbridge_service.py` with: `publish_evaluation_event(evaluation_id, candidate_position_id, step_type, source_document_id, rubric_version_id)` — calls EventBridge `PutEvents` with the event structure from tech spec. Skip silently if `EVALUATION_EVENT_BUS_NAME` is empty (local dev graceful degradation) **[Agent: python-architect]**
  - [x] Add `trigger_evaluation(session, candidate_position_id, step_type, source_document_id, rubric_version_id)` to `evaluation_service.py` — creates Evaluation row with `status=pending`, then calls `eventbridge_service.publish_evaluation_event()`. Determine next `version` number by querying max existing version for that (candidate_position_id, step_type) **[Agent: python-architect]**
  - [x] Modify `document_service.complete_upload()` — after setting `status=active`, determine step_type from document (`cv` → `cv_analysis`; `transcript` + `screening` → `screening_eval`; `transcript` + `technical` → `technical_eval`). For `technical_eval`, check if position has a rubric — skip if missing. Call `evaluation_service.trigger_evaluation()` **[Agent: python-architect]**
  - [x] Modify `document_service.create_pasted_transcript()` — same trigger logic as `complete_upload` after the document is created as `active` **[Agent: python-architect]**
  - [x] Write tests: mock boto3 EventBridge client; test that completing a CV upload creates a `cv_analysis` evaluation with `status=pending`; test that completing a technical transcript upload with no rubric does NOT create an evaluation; test that EventBridge is skipped when `EVALUATION_EVENT_BUS_NAME` is empty **[Agent: typescript-test-expert]**
  - [x] Run `uv run pytest`, `uv run ruff check .`, `uv run mypy app/` — all pass **[Agent: python-architect]**
  - [x] **Verify:** Start the app, upload a CV via the frontend for a candidate+position. Check DB: `SELECT * FROM evaluations` — should see a row with `step_type=cv_analysis`, `status=pending`. No errors in backend logs. App is fully functional. **[Agent: general-purpose]**

---

## Slice 3: Lambda shared layer + cv-analysis Lambda

> First Lambda. Shared infra (DB, Bedrock, prompts). cv_analysis handler reads CV from S3, calls Bedrock, writes result to evaluations table.

- [x] **Slice 3: Lambda shared layer and cv-analysis function**
  - [x] Create directory structure: `app/lambdas/shared/`, `app/lambdas/cv_analysis/` **[Agent: python-architect]**
  - [x] Create `app/lambdas/shared/config.py` — reads DB connection params from SSM Parameter Store at cold start (DB_HOST, DB_PORT, DB_NAME, DB_USERNAME, DB_PASSWORD), caches in module-level variables. Falls back to env vars for local testing **[Agent: python-architect]**
  - [x] Create `app/lambdas/shared/db.py` — sync SQLAlchemy engine factory using config params. Provides `get_session()` context manager yielding a sync `Session`. Connection pool: `pool_size=1, max_overflow=0` (single-connection per Lambda) **[Agent: python-architect]**
  - [x] Create `app/lambdas/shared/bedrock.py` — boto3 Bedrock Runtime client wrapper. `invoke_claude(prompt, max_tokens, system_prompt)` → calls `invoke_model` with Claude model ID (configurable via env var `BEDROCK_MODEL_ID`), returns parsed response text. Handles throttling with exponential backoff (3 retries) **[Agent: python-architect]**
  - [x] Create `app/lambdas/shared/models.py` — imports and re-exports the `Evaluation`, `Document`, `CandidatePosition`, `Position`, `PositionRubric`, `PositionRubricVersion` SQLModel models for use by Lambda handlers **[Agent: python-architect]**
  - [x] Create `app/lambdas/shared/s3.py` — `get_document_text(s3_key)` → reads document content from S3. For PDF: extract text (use `pypdf` or similar lightweight library). For plain text/markdown: return as-is. For DOCX: extract text (use `python-docx`) **[Agent: python-architect]**
  - [x] Create `app/lambdas/shared/prompts/cv_analysis.py` — prompt template for CV analysis. Takes position requirements (title, description, skills) + CV text. Instructs Claude to return structured JSON matching the `cv_analysis` result schema **[Agent: python-architect]**
  - [x] Create `app/lambdas/cv_analysis/handler.py` — Lambda entry point `def handler(event, context)`. Flow: (1) read `evaluation_id` from event, (2) update evaluation `status=running, started_at=now()`, (3) load document from S3 via s3_key, (4) load position requirements via candidate_position → position join, (5) build prompt, (6) call Bedrock, (7) parse JSON response, (8) update evaluation `status=completed, result={...}, completed_at=now()`, (9) return result for Step Functions. On error: update `status=failed, error_message=str(e)`, re-raise for Step Functions retry **[Agent: python-architect]**
  - [x] Create `app/lambdas/requirements.txt` — shared dependencies: `sqlalchemy`, `psycopg2-binary`, `boto3`, `pypdf`, `python-docx` **[Agent: python-architect]**
  - [x] Write unit tests for cv_analysis handler: mock DB session, mock S3 client (return sample CV text), mock Bedrock client (return valid JSON). Verify evaluation row updated to `completed` with correct result structure. Test error case: verify status set to `failed` with error message **[Agent: python-architect]**
  - [x] Write unit tests for shared modules: `s3.get_document_text()` with plain text and PDF mocks; `bedrock.invoke_claude()` with mock responses; `config` reading from env vars **[Agent: python-architect]**
  - [x] **Verify:** Run Lambda handler locally with test event (`{"evaluation_id": 1}`) against local Postgres + MinIO. Verify evaluation row updated in DB with `status=completed` and valid `result` JSONB. **[Agent: general-purpose]**

---

## Slice 4: Step Functions state machine + EventBridge rule (cv-analysis wired)

> Terraform infra: EventBridge rule → Step Functions → cv-analysis Lambda. First full loop: upload CV → event → state machine → Lambda → DB result.

- [x] **Slice 4: Step Functions + EventBridge Terraform infra**
  - [x] Create `infra/modules/evaluation-pipeline/` or add resources to existing infra structure — follow existing Terraform patterns in the repo **[Agent: terraform-infrastructure]**
  - [x] Create EventBridge custom event bus: `lauter-evaluation-events` **[Agent: terraform-infrastructure]**
  - [x] Create EventBridge rule: matches `source = "lauter.api"`, `detail-type = "evaluation.requested"`, target = Step Functions state machine **[Agent: terraform-infrastructure]**
  - [x] Create IAM role for EventBridge → Step Functions: allows `states:StartExecution` on the state machine ARN **[Agent: terraform-infrastructure]**
  - [x] Create Lambda function for `cv-analysis`: Python 3.12 runtime, 512MB memory, 5min timeout, VPC-attached (same subnets/SGs as ECS), environment variables for `BEDROCK_MODEL_ID` and `S3_BUCKET_NAME`. Source from `app/lambdas/cv_analysis/` **[Agent: terraform-infrastructure]**
  - [x] Create Lambda layer for shared code: packages `app/lambdas/shared/` + dependencies from `requirements.txt` **[Agent: terraform-infrastructure]**
  - [x] Create IAM role for cv-analysis Lambda: `bedrock:InvokeModel`, `s3:GetObject` on files bucket, `ssm:GetParameter` for DB params, `logs:CreateLogGroup/CreateLogStream/PutLogEvents`, VPC execution role (`ec2:CreateNetworkInterface`, etc.) **[Agent: terraform-infrastructure]**
  - [x] Create Lambda security group: outbound to RDS security group on port 5432, outbound to NAT Gateway (for Bedrock) **[Agent: terraform-infrastructure]**
  - [x] Create Step Functions state machine `evaluation-pipeline` (Standard workflow): initial version with `RouteByStepType` Choice state → `InvokeCvAnalysis` Task state (invokes cv-analysis Lambda) → End. Add Retry (2 attempts, exponential backoff) and Catch (transition to `MarkCvAnalysisFailed` Pass state that outputs error info) on the Task state **[Agent: terraform-infrastructure]**
  - [x] Create IAM role for Step Functions: allows `lambda:InvokeFunction` on evaluation Lambda ARNs, `logs:*` for execution logging **[Agent: terraform-infrastructure]**
  - [x] Create SSM parameters for DB connection if not already provisioned (reuse existing ECS params if available) **[Agent: terraform-infrastructure]**
  - [x] Add `EVALUATION_EVENT_BUS_NAME` env var to backend ECS task definition **[Agent: terraform-infrastructure]**
  - [x] Run `terraform fmt -recursive`, `terraform validate`, `terraform plan -var-file="terraform.tfvars"` — verify no errors, review plan output **[Agent: terraform-infrastructure]**
  - [x] **Verify:** After `terraform apply`: upload a CV via the SPA → check CloudWatch Logs for EventBridge event delivery → check Step Functions console for execution → check Lambda logs → check DB for evaluation with `status=completed` and `result` populated. Full end-to-end loop working. **[Agent: general-purpose]**

---

## Slice 5: screening-eval Lambda

> Second Lambda. Process screening transcripts into structured summaries.

- [x] **Slice 5: screening-eval Lambda function**
  - [x] Create `app/lambdas/shared/prompts/screening_eval.py` — prompt template: takes position requirements + screening transcript text. Instructs Claude to return structured JSON with keys: `key_topics`, `strengths`, `concerns`, `communication_quality`, `motivation_culture_fit`. Each is a list of strings or a narrative string per the result schema **[Agent: python-architect]**
  - [x] Create `app/lambdas/screening_eval/handler.py` — Lambda entry point. Flow: (1) read `evaluation_id`, (2) mark `running`, (3) load transcript document text from S3, (4) load position requirements, (5) build prompt, (6) call Bedrock, (7) validate response has all 5 sections, (8) write `completed` with result. Error handling: if transcript < 100 words, fail with "Transcript too short for meaningful analysis" **[Agent: python-architect]**
  - [x] Add Terraform resource: `aws_lambda_function` for `screening-eval`, same config as cv-analysis (512MB, 5min, VPC, shared layer). Add to Step Functions state machine: new `InvokeScreeningEval` Task state in the `screening_eval` Choice branch **[Agent: terraform-infrastructure]**
  - [x] Write unit tests: mock Bedrock response, verify all 5 sections present in result. Test short transcript rejection (<100 words → failed status). Test normal flow → completed status with valid result **[Agent: python-architect]**
  - [x] **Verify:** Upload a screening transcript for a candidate+position. Check DB: evaluation with `step_type=screening_eval`, `status=completed`, `result` containing all 5 structured sections. **[Agent: general-purpose]**

---

## Slice 6: technical-eval Lambda

> Rubric-scored evaluation. Reads position rubric version, scores each criterion 1-5 with evidence.

- [x] **Slice 6: technical-eval Lambda function**
  - [x] Create `app/lambdas/shared/prompts/technical_eval.py` — prompt template: takes rubric structure (categories, criteria with weights), position requirements, + technical transcript. Instructs Claude to score each criterion 1-5 with evidence quotes and reasoning. Return structured JSON matching `technical_eval` result schema: `criteria_scores[]`, `weighted_total`, `strengths_summary[]`, `improvement_areas[]` **[Agent: python-architect]**
  - [x] Create `app/lambdas/technical_eval/handler.py` — Lambda entry point. Flow: (1) read `evaluation_id`, (2) mark `running`, (3) load transcript from S3, (4) load position requirements, (5) load rubric version via `rubric_version_id` from evaluation row → get `structure` JSONB, (6) build prompt with rubric criteria, (7) call Bedrock, (8) parse response, (9) calculate `weighted_total` from criteria scores × weights (verify server-side, don't trust LLM math), (10) write `completed` with result. Error: if `rubric_version_id` is null → fail with "No rubric assigned" **[Agent: python-architect]**
  - [x] Add Terraform resource: `aws_lambda_function` for `technical-eval`. Add to Step Functions: `InvokeTechnicalEval` Task state in the `technical_eval` Choice branch **[Agent: terraform-infrastructure]**
  - [x] Write unit tests: mock Bedrock with scored criteria, verify `weighted_total` is server-calculated correctly (not the LLM value). Test missing rubric → failed. Test normal flow with 3 criteria → completed with all scores **[Agent: python-architect]**
  - [x] **Verify:** Assign a rubric to a position, upload a technical transcript. Check DB: evaluation with `step_type=technical_eval`, `status=completed`, `result.weighted_total` correctly calculated, all criteria scored. **[Agent: general-purpose]**

---

## Slice 7: recommendation Lambda (aggregation + fault tolerance)

> Reads all prior step results. Generates hire/no-hire recommendation. Handles missing inputs gracefully.

- [x] **Slice 7: recommendation Lambda with aggregation**
  - [x] Create `app/lambdas/shared/prompts/recommendation.py` — prompt template: takes aggregated inputs (cv_analysis result, screening_eval result, technical_eval result — any may be null/missing). Instructs Claude to produce: `recommendation` (hire/no_hire/needs_discussion), `confidence` (high/medium/low), `reasoning` (narrative referencing evidence), `missing_inputs` (list of unavailable steps). Explicitly instruct: if any input is missing, confidence must be capped at "low" **[Agent: python-architect]**
  - [x] Create `app/lambdas/recommendation/handler.py` — Lambda entry point. Flow: (1) read `evaluation_id`, (2) mark `running`, (3) query latest completed evaluations for the same `candidate_position_id` for step types `cv_analysis`, `screening_eval`, `technical_eval`, (4) collect available results + note missing ones, (5) build prompt with available data, (6) call Bedrock, (7) validate response (recommendation must be one of 3 values, confidence one of 3), (8) write `completed`. Never fail due to missing upstream data — that's expected **[Agent: python-architect]**
  - [x] Update Step Functions state machine: after `InvokeTechnicalEval` succeeds or fails, transition to `InvokeRecommendation`. Add `InvokeRecommendation` as standalone branch for `recommendation` step type. Add cascade logic: after `InvokeCvAnalysis` and `InvokeScreeningEval`, add `CheckRecommendationCascade` Choice state that checks if a `technical_eval` result exists for this candidate_position — if yes, trigger recommendation; if no, end **[Agent: terraform-infrastructure]**
  - [x] Write unit tests: test with all 3 inputs available → recommendation with confidence high/medium. Test with only technical_eval available → recommendation with confidence "low" and `missing_inputs` listing cv_analysis and screening_eval. Test with no inputs at all → still produces a recommendation with low confidence **[Agent: python-architect]**
  - [x] **Verify:** Upload a technical transcript (with rubric assigned). Check DB: both `technical_eval` and `recommendation` evaluations created. Recommendation references technical eval scores. Then test fault tolerance: create a scenario where cv_analysis failed — recommendation should still complete, noting missing input. **[Agent: general-purpose]**

---

## Slice 8: feedback-gen Lambda + rejection trigger

> Generate candidate rejection feedback. Wire HM "Reject" action to trigger feedback generation.

- [x] **Slice 8: feedback-gen Lambda and rejection trigger**
  - [x] Create `app/lambdas/shared/prompts/feedback_gen.py` — prompt template: takes available evaluation results + rejection stage (screening/technical). Instructs Claude to produce professional, constructive feedback. Explicit rules: do NOT expose numeric scores, rubric criteria names, or internal evaluation details. Must mention at least one strength. Must provide actionable improvement areas **[Agent: python-architect]**
  - [x] Create `app/lambdas/feedback_gen/handler.py` — Lambda entry point. Flow: (1) read `evaluation_id`, (2) mark `running`, (3) load all available evaluations for the candidate_position, (4) determine rejection stage from evaluation metadata, (5) build prompt, (6) call Bedrock, (7) write `completed` with `{feedback_text, rejection_stage}` **[Agent: python-architect]**
  - [x] Add `trigger_feedback_gen(session, candidate_position_id)` to `evaluation_service.py` — creates a `feedback_gen` evaluation and publishes EventBridge event **[Agent: python-architect]**
  - [x] Modify `candidate_service.update_stage()` or the candidates router — when a stage transition results in `rejected`, call `evaluation_service.trigger_feedback_gen()` **[Agent: python-architect]**
  - [x] Add Terraform resource: `aws_lambda_function` for `feedback-gen`. Add to Step Functions: `InvokeFeedbackGen` Task state in the `feedback_gen` Choice branch **[Agent: terraform-infrastructure]**
  - [x] Write unit tests: test feedback doesn't contain numeric scores or criterion names (regex/string check). Test that rejecting a candidate at screening stage creates a `feedback_gen` evaluation. Test normal flow → feedback text generated with at least one strength mention **[Agent: python-architect]**
  - [x] **Verify:** In the SPA, change a candidate's stage to "rejected". Check DB: `feedback_gen` evaluation created, `status=completed`, `result.feedback_text` is professional and doesn't expose internal scores. **[Agent: general-purpose]**

---

## Slice 9: Re-run endpoint + cascading

> API endpoint to re-run any evaluation step. Creates new version, triggers downstream dependents.

- [x] **Slice 9: Re-run with version incrementing and cascading**
  - [x] Add `rerun_evaluation(session, candidate_position_id, step_type)` to `evaluation_service.py` — (1) query max version for the (candidate_position_id, step_type) pair, (2) create new Evaluation row with `version = max + 1`, `status=pending`, (3) publish EventBridge event. For cascading: also create pending evaluations for downstream dependents (cv_analysis/screening_eval/technical_eval → recommendation if technical_eval exists; technical_eval → recommendation always) **[Agent: python-architect]**
  - [x] Add `POST /api/evaluations/{candidate_position_id}/{step_type}/rerun` endpoint to evaluations router. Returns the newly created evaluation(s). Requires auth **[Agent: python-architect]**
  - [x] Write tests: rerun cv_analysis → new version created, if technical_eval v1 exists then recommendation also gets new pending version. Rerun technical_eval → recommendation also gets new pending version. Verify old versions preserved (query history endpoint returns multiple versions) **[Agent: python-architect]**
  - [x] Run `uv run pytest`, `uv run ruff check .`, `uv run mypy app/` **[Agent: python-architect]**
  - [x] Regenerate OpenAPI spec + frontend client **[Agent: python-architect]**
  - [x] **Verify:** Via curl: POST `/api/evaluations/1/cv_analysis/rerun` → new evaluation created with version 2. GET `/api/evaluations/1/cv_analysis/history` → returns both v1 and v2. Step Functions triggers and processes the new evaluation. **[Agent: general-purpose]**

---

## Slice 10: SSE endpoint for live status updates

> Server-Sent Events streaming endpoint. Frontend will consume this in the next slice.

- [x] **Slice 10: SSE streaming endpoint**
  - [x] Add `sse-starlette` dependency: `cd app/backend && uv add sse-starlette` **[Agent: python-architect]**
  - [x] Add `GET /api/evaluations/{candidate_position_id}/stream` endpoint to evaluations router. Uses `EventSourceResponse` from sse-starlette. Implementation: async generator that (1) queries evaluations with `status in (pending, running)` for the candidate_position, (2) tracks last-known status per evaluation_id, (3) on each poll iteration (every 2-3s), checks for status changes, (4) yields `event: status_change` with `{evaluation_id, step_type, status}` data for each change, (5) sends `: keepalive` comment every 30s if no changes, (6) yields `event: done` and exits when all evaluations are terminal (completed/failed) or none exist. Requires auth (read cookie from request before starting stream) **[Agent: python-architect]**
  - [x] Write tests: test SSE endpoint returns `text/event-stream` content type. Test that status changes are emitted correctly (create evaluation as pending, update to running in background, verify event emitted). Test that `done` event is sent when all terminal. Test keepalive behavior **[Agent: python-architect]**
  - [x] Run full test suite + linters **[Agent: python-architect]**
  - [x] Regenerate OpenAPI spec + frontend client (note: SSE endpoint may need manual client code since hey-api may not handle streaming) **[Agent: python-architect]**
  - [x] **Verify:** Via curl: `curl -N http://localhost:8000/api/evaluations/1/stream` (with auth cookie). Upload a document for candidate_position 1 in another terminal. Observe SSE events streaming: `event: status_change` as evaluation progresses. Connection closes after `event: done`. **[Agent: general-purpose]**

---

## Slice 11: Frontend — evaluation display + SSE live updates

> Core frontend: evaluation hooks, SSE connection, status badges, toast notifications on candidate page.

- [x] **Slice 11: Evaluation display with live SSE updates**
  - [x] Install sonner: `cd app/frontend && bunx shadcn@latest add sonner`. Add `<Toaster />` to the app root layout (likely `src/routes/__root.tsx` or equivalent) **[Agent: react-architect]**
  - [x] Create `src/shared/lib/evaluation-utils.ts` — `getEvaluationStepLabel(stepType)` mapping (`cv_analysis` → "CV Analysis", etc.); `getEvaluationStatusVariant(status)` mapping (`pending` → "secondary", `running` → "default", `completed` → "default", `failed` → "destructive"); `formatEvaluationStatus(status)` for human-readable labels **[Agent: react-architect]**
  - [x] Create `src/features/evaluations/hooks/use-evaluations.ts` — `useQuery` calling `GET /api/evaluations/{candidatePositionId}`. Returns list of latest evaluations per step **[Agent: react-architect]**
  - [x] Create `src/features/evaluations/hooks/use-evaluation-stream.ts` — custom hook wrapping `EventSource`. Opens connection to `/api/evaluations/{candidatePositionId}/stream` when any evaluation is `pending` or `running`. On `status_change` event: (1) show toast via sonner (`toast.success("CV Analysis completed")` or `toast.error("Screening eval failed")`), (2) invalidate `use-evaluations` query to refetch full results. On `done` event: close connection. Clean up on unmount. Handle reconnection on connection drop **[Agent: react-architect]**
  - [x] Create `src/widgets/evaluations/evaluation-step-card.tsx` — renders a single evaluation step: step name label (from evaluation-utils), status `Badge` (variant from evaluation-utils), completion timestamp (if completed), error message with red text (if failed), placeholder for result content (to be filled in Slice 12). Use `Card` from shadcn **[Agent: react-architect]**
  - [x] Create `src/widgets/evaluations/evaluation-results.tsx` — container component. Takes `candidatePositionId` prop. Calls `use-evaluations` to fetch data + `use-evaluation-stream` for live updates. Renders list of `EvaluationStepCard` components, ordered: cv_analysis → screening_eval → technical_eval → recommendation → feedback_gen (only show steps that exist). Show empty state "No evaluations yet" if list is empty **[Agent: react-architect]**
  - [x] Mount `EvaluationResults` on the candidate detail page (`src/routes/_authenticated/candidates/$candidateId.tsx`). Place between the positions table and documents section. Determine which `candidatePositionId` to show — if candidate has one position, use that; if multiple, show evaluations for the position selected/highlighted in the positions table (may need local state coordination) **[Agent: react-architect]**
  - [x] Run `bun run build` and `bun run lint` — verify no errors **[Agent: react-architect]**
  - [x] **Verify:** Open candidate page in browser. Upload a CV. Observe: (1) evaluation card appears with "Pending" badge, (2) badge transitions to "Running", (3) toast notification appears when complete, (4) badge shows "Completed" with timestamp. No page refresh needed. **[Agent: general-purpose]**

---

## Slice 12: Frontend — step result renderers

> Per-step result display components. Each renders the structured JSONB into readable UI.

- [x] **Slice 12: Evaluation result display components**
  - [x] Create `src/widgets/evaluations/cv-analysis-result.tsx` — renders CV analysis result JSONB: skills match as a table (skill name, present/absent badge, notes), experience relevance as paragraph, education as paragraph, signals/red flags as bullet list with color coding (green for positive, amber for concerns), overall fit as summary paragraph **[Agent: react-architect]**
  - [x] Create `src/widgets/evaluations/screening-eval-result.tsx` — renders screening summary: 5 labeled sections each as a collapsible area or card section. Key topics as bullet list, strengths as green-tinted bullet list, concerns as amber-tinted bullet list, communication quality as paragraph, motivation/culture fit as paragraph **[Agent: react-architect]**
  - [x] Create `src/widgets/evaluations/technical-eval-result.tsx` — renders rubric scores: (1) weighted total score prominently displayed (e.g., "3.8 / 5.0" with a progress bar), (2) criteria table with columns: category, criterion, score (with visual bar 1-5), weight, evidence (expandable), reasoning (expandable), (3) strengths summary as green-tinted list, (4) improvement areas as amber-tinted list **[Agent: react-architect]**
  - [x] Create `src/widgets/evaluations/recommendation-result.tsx` — renders recommendation: (1) large recommendation badge (Hire = green, No Hire = red, Needs Discussion = amber), (2) confidence level badge (High/Medium/Low), (3) reasoning as formatted paragraph, (4) missing data callout in a warning banner if `missing_inputs` is non-empty **[Agent: react-architect]**
  - [x] Create `src/widgets/evaluations/feedback-draft-result.tsx` — renders feedback text in a styled container. Includes an "Edit" button that switches to a textarea for HM to modify the draft. "Save" persists edits (API endpoint TBD — may store locally for now or add a PATCH endpoint) **[Agent: react-architect]**
  - [x] Update `evaluation-step-card.tsx` — import and render the appropriate result component based on `step_type` when `status === "completed"`. Map: `cv_analysis` → `CvAnalysisResult`, `screening_eval` → `ScreeningEvalResult`, etc. Pass `result` JSONB as prop **[Agent: react-architect]**
  - [x] Run `bun run build` and `bun run lint` **[Agent: react-architect]**
  - [x] **Verify:** With existing evaluations in the DB (from previous slices), open candidate page. Verify each evaluation type renders its results correctly — skills match table, rubric scores with bars, recommendation badge. Check responsive layout on different screen sizes. **[Agent: general-purpose]**

---

## Slice 13: Frontend — re-run + HM decision gate

> Re-run button on evaluation cards. HM proceed/reject decision buttons with notes.

- [x] **Slice 13: Re-run evaluations and HM decision gate**
  - [x] Create `src/features/evaluations/hooks/use-rerun-evaluation.ts` — `useMutation` calling `POST /api/evaluations/{candidatePositionId}/{stepType}/rerun`. On success: invalidate `use-evaluations` query, show toast "Re-running [step name]..." **[Agent: react-architect]**
  - [x] Update `evaluation-step-card.tsx` — add "Re-run" button (secondary variant) visible when evaluation is `completed` or `failed`. Button triggers `useRerunEvaluation` mutation. Show loading spinner during mutation. Disable button while any evaluation for this candidate_position is `pending` or `running` (prevent conflicting runs) **[Agent: react-architect]**
  - [x] Create `src/widgets/evaluations/hm-decision-gate.tsx` — component shown contextually: (1) after screening_eval completes: "Proceed to Technical" (primary) and "Reject" (destructive) buttons, (2) after recommendation completes: "Hire" (primary) and "Reject" (destructive) buttons. Each button opens a confirmation dialog with optional notes textarea. "Proceed to Technical" calls existing stage transition API (`screening` → `technical`). "Reject" calls stage transition to `rejected`. "Hire" calls stage transition to `offer` or `hired` (depending on current stage). On rejection: the backend auto-triggers feedback-gen (from Slice 8) **[Agent: react-architect]**
  - [x] Mount `HmDecisionGate` in `evaluation-results.tsx` — rendered after the relevant evaluation step card, only when the evaluation is completed and no decision has been made yet (check current pipeline stage from candidate_position) **[Agent: react-architect]**
  - [x] Run `bun run build` and `bun run lint` **[Agent: react-architect]**
  - [x] **Verify:** Open candidate page with completed evaluations. (1) Click "Re-run" on cv-analysis → new evaluation appears as pending, processes, replaces old result. (2) After screening_eval completes, "Proceed to Technical" and "Reject" buttons appear. Click "Reject" with a note → candidate stage changes to rejected, feedback-gen evaluation appears. (3) Verify "Re-run" button is disabled while another evaluation is in progress. **[Agent: general-purpose]**

---

## Slice 14: Frontend — evaluation history (audit trail)

> Version history for each evaluation step. Accessible from the step card.

- [x] **Slice 14: Evaluation version history**
  - [x] Create `src/features/evaluations/hooks/use-evaluation-history.ts` — `useQuery` calling `GET /api/evaluations/{candidatePositionId}/{stepType}/history`. Returns all versions ordered by version desc **[Agent: react-architect]**
  - [x] Create `src/widgets/evaluations/evaluation-history-dialog.tsx` — dialog showing all versions of a specific evaluation step. List view with: version number, status badge, timestamp, truncated result preview. Click a version to expand and see full result (reuse the step-specific result renderer from Slice 12). Current/latest version highlighted **[Agent: react-architect]**
  - [x] Update `evaluation-step-card.tsx` — add "History" link/button (subtle, secondary) next to the "Re-run" button. Only visible when `version > 1` (multiple versions exist). Opens `EvaluationHistoryDialog` **[Agent: react-architect]**
  - [x] Run `bun run build` and `bun run lint` **[Agent: react-architect]**
  - [x] **Verify:** Re-run an evaluation step so multiple versions exist. Open candidate page, click "History" on that step. Dialog shows both versions with correct data. Older version is accessible but latest is highlighted. **[Agent: general-purpose]**

---

## Subagent Coverage

| Technology | Assigned Agent | Status |
|---|---|---|
| Python / FastAPI (backend) | `python-architect` | ✅ Available |
| React / TypeScript (frontend) | `react-architect` | ✅ Available |
| Terraform / AWS infra | `terraform-infrastructure` | ✅ Available |
| Lambda (Python) | `python-architect` (fallback) | ⚠️ No dedicated Lambda agent |
| Step Functions (ASL) | `terraform-infrastructure` (fallback) | ⚠️ No dedicated SFN agent |
| Verification / E2E | `general-purpose` | ⚠️ No dedicated QA agent |

| Task Area | Issue | Recommendation |
|---|---|---|
| Lambda handlers (Slices 3-8) | Assigned to `python-architect` — no dedicated serverless agent | Acceptable — Python patterns are the same; `python-architect` handles this well |
| Step Functions ASL (Slice 4, 5-8) | State machine JSON definition assigned to `terraform-infrastructure` | Acceptable — ASL is defined in Terraform; `terraform-infrastructure` handles IaC |
| Verification steps (all slices) | Assigned to `general-purpose` — no QA specialist | Consider installing Playwright MCP for browser-based UI verification. Currently, verification relies on curl + DB queries + manual browser checks |
