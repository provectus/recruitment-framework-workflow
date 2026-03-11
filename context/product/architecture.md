# System Architecture Overview: Recruitment Workflow POC

- **Version:** 5.0
- **Status:** Revised — Lambda + Step Functions replaces n8n; manual-first POC, Lever deferred

---

## 1. Application & Technology Stack

- **Frontend:** React + TypeScript SPA (Vite) — recruiter-facing UI for candidate/position management, rubric management, transcript/CV upload, and evaluation tracking
- **Backend API:** Python + FastAPI — API layer between SPA, evaluation pipeline, and external services
- **Evaluation Pipeline:** AWS Step Functions + Lambda (Python 3.12) — orchestrates multi-step candidate evaluation; one Lambda per evaluation step
- **Event Bus:** Amazon EventBridge — decouples FastAPI from the evaluation pipeline; API publishes evaluation events, EventBridge rules route to Step Functions
- **Authentication:** Google OAuth 2.0 (corporate Google Workspace)

---

## 2. External Services & APIs

- **Interview Recordings & Transcripts:** Barley — sync recordings and transcripts from Barley's S3 storage, filtered to recruitment interviews only (access pattern TBD)
- **AI Engine:** Claude via Amazon Bedrock — CV analysis, transcript processing, rubric evaluation, feedback generation
- **Identity Provider:** Google Workspace (OAuth 2.0)

**Future (deferred):**
- **ATS (Applicant Tracking):** Lever API — pull candidate data + feedback form schemas, push evaluation notes + approved feedback forms back. Timing depends on POC results and Lever access readiness.
- **AI Candidate Analyst:** Claude Agent SDK (ECS Fargate) — conversational recruiter assistant with custom MCP tools for querying evaluations, fetching CVs/transcripts, and comparing candidates

---

## 3. Data & Persistence

- **Primary Database:** PostgreSQL (AWS RDS) — candidates, positions, evaluations, artifacts, rubrics, users, audit trail
- **File Storage:** AWS S3 — uploaded transcripts, recordings, and CVs (written by API, presigned URLs for upload/download)
- **Prompt Templates:** Version-controlled files in repository (packaged into Lambda deployment artifacts)
- **Candidate Source of Truth:** PostgreSQL (manual entry via SPA; Lever sync planned for future)

**Data Model:**
```
User (1) → Uploads (many)
Position (1) → Candidates (many)
  - Manually created: title, requirements, team, hiring manager
Candidate (1) → Artifacts (many)
  - CV upload + analysis result
  - Screening transcript + summary (from Barley sync or manual upload)
  - Technical transcript + evaluation (from Barley sync or manual upload)
  - Final recommendation
  - Feedback draft (candidate-facing)
Interview (many) → Candidate (1)
  - Type: screening | technical
  - Source: barley_sync | manual_upload
  - Transcript text, recording URL (if Barley)
  - Linked to position and interviewer
RubricTemplate (many, standalone)
  - Reusable evaluation framework: name, description, structure (JSONB)
  - Soft-deleted via is_archived
Position (1) → PositionRubric (0..1)
  - Links position to its evaluation rubric, tracks source template
  PositionRubric (1) → PositionRubricVersions (many)
    - Append-only JSONB snapshots: structure, version_number, created_by
Evaluation (1) → Audit Log (many)
```

**Future additions (when Lever integrates):**
```
Position (1) → FeedbackFormTemplates (many)
  - Lever form schema per interview stage
Candidate (1) → FeedbackFormDrafts (many)
  - AI-drafted Lever form responses per interviewer assignee
  - Review status: draft → approved → submitted
```

---

## 4. Infrastructure & Deployment

### AWS Cloud
- **Backend API:** ECS Fargate (FastAPI Docker container)
- **Frontend SPA:** S3 + CloudFront (static hosting)
- **Database:** RDS PostgreSQL (private subnet)
- **File Storage:** S3 (private bucket, presigned URLs for upload/download)
- **Event Bus:** Amazon EventBridge (custom event bus for evaluation events)
- **Workflow Orchestration:** AWS Step Functions (Standard workflow — orchestrates evaluation pipeline)
- **Evaluation Lambdas:** 5× AWS Lambda (Python 3.12) — one per evaluation step, VPC-attached for RDS access
- **AI:** Amazon Bedrock (Claude, us-east-1)
- **Region:** us-east-1

### Lambda Functions
| Lambda | Responsibility |
|--------|---------------|
| `cv-analysis` | Parse CV from S3, compare against role requirements via Bedrock, write analysis result to RDS |
| `screening-eval` | Process screening transcript, generate structured summary via Bedrock, write to RDS |
| `technical-eval` | Evaluate technical interview against rubric via Bedrock, write scored evaluation to RDS |
| `recommendation` | Aggregate step scores, generate hire/no-hire recommendation via Bedrock, write to RDS |
| `feedback-gen` | Generate candidate-facing rejection feedback via Bedrock, write draft to RDS |

### Lambda Configuration
- **Runtime:** Python 3.12
- **Timeout:** 5 minutes (Bedrock calls can be slow for long transcripts)
- **Memory:** 512 MB (adjustable per function)
- **VPC:** Same VPC as ECS/RDS — Lambdas need direct RDS access
- **Layers:** Shared layer for common dependencies (boto3 Bedrock client, SQLAlchemy/asyncpg, prompt utilities)
- **IAM:** Each Lambda gets least-privilege role: Bedrock InvokeModel, S3 GetObject, RDS connect, CloudWatch Logs

---

## 5. Communication Flow

```
                        ┌──────────────┐
                        │  Barley S3   │
                        │ (recordings/ │
                        │ transcripts) │
                        └──────┬───────┘
                               │ sync (access TBD)
┌──────────────────────────────┼──────────────────────────────────┐
│  AWS Cloud (us-east-1)       │                                  │
│                              │                                  │
│  ┌─────────────────────┐  ┌──┴───────┐   ┌──────────────────┐  │
│  │ React SPA           │──│ FastAPI  │   │ EventBridge      │  │
│  │ (S3 + CloudFront)   │  │ (ECS)    │──►│ (custom bus)     │  │
│  └─────────────────────┘  └────┬─────┘   └───────┬──────────┘  │
│                                │                  │              │
│                           ┌────┴─────┐   ┌───────┴──────────┐  │
│                           │ RDS      │   │ Step Functions   │  │
│                           │ Postgres │◄──│ (state machine)  │  │
│                           └──────────┘   └───────┬──────────┘  │
│                                                  │              │
│  ┌──────┐  ┌───────────┐  ┌──────────────────────┴───────────┐ │
│  │  S3  │  │ Bedrock   │  │         Lambda Functions          │ │
│  │(files)│  │ (Claude)  │◄─│ cv-analysis | screening-eval     │ │
│  └──────┘  └───────────┘  │ technical-eval | recommendation   │ │
│                           │ feedback-gen                      │ │
│                           └──────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
```

**Request flow (POC):**
1. Recruiter logs into SPA via Google OAuth
2. Creates candidates and positions manually in the SPA
3. Uploads CV via SPA → FastAPI → S3
4. Uploads transcript manually or system syncs from Barley S3
5. FastAPI creates evaluation record in Postgres (status: `pending`)
6. FastAPI publishes evaluation event to EventBridge (event type: `evaluation.requested`, payload: evaluation ID, step type)
7. EventBridge rule matches event and starts Step Functions execution
8. Step Functions orchestrates Lambda sequence: each Lambda reads input from previous step, calls Bedrock, writes results directly to RDS Postgres
9. Step Functions execution completes (success/failure logged)
10. SPA polls FastAPI for updates — recruiter sees evaluation results (Lambdas have already written to DB)

**Future addition (when Lever integrates):**
- FastAPI syncs candidate/position data from Lever instead of manual entry
- Evaluation notes and approved feedback forms pushed back to Lever

---

## 6. Step Functions State Machine

### `evaluation-pipeline` (Standard Workflow)

The state machine supports multiple entry points — not every evaluation runs all steps. The triggering event specifies which step(s) to execute.

**Full pipeline flow (technical candidate):**
```
Start → cv-analysis → screening-eval → technical-eval → recommendation → End
```

**Individual step invocations:**
- CV uploaded → `cv-analysis` only
- Screening transcript uploaded → `screening-eval` only
- Technical transcript uploaded → `technical-eval` → `recommendation`
- Rejection decision → `feedback-gen`

Each step is a Task state invoking its corresponding Lambda. Error handling via Step Functions Catch/Retry — failed steps retry 2× with exponential backoff, then transition to a `Failed` terminal state that updates the evaluation record.

**Future (when Lever integrates):**

| Step | Description |
|------|-------------|
| `feedback-form-draft` | Pull Lever form schema, draft form responses via Claude from transcript |
| `lever-sync` | Push evaluation notes + approved feedback forms back to Lever |

---

## 7. Observability & Monitoring

- **API Logging:** CloudWatch Logs (FastAPI container logs)
- **Lambda Logging:** CloudWatch Logs (one log group per Lambda function)
- **Step Functions:** Execution history with visual workflow inspector — shows each step's input/output, duration, and errors
- **Metrics/Alerts:** CloudWatch Metrics (API health, Lambda duration/errors/throttles, Step Functions execution success/failure rate)
- **Tracing:** Request IDs passed from SPA → API → EventBridge → Step Functions → Lambdas (correlation via evaluation ID)
- **Cost Monitoring:** Lambda invocation count + duration, Bedrock token usage per evaluation

---

## 8. Key Architectural Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Manual-first POC | Manual candidate/position/transcript entry | Decouples POC from Lever timeline; proves evaluation pipeline independently |
| SPA instead of Slack-only | React + TS | Recruiters need upload UX + candidate management + evaluation tracking |
| Python backend | FastAPI | Team preference, async support, good typing, fast dev |
| ~~n8n on-prem~~ | ~~Docker Compose~~ | ~~Purchased instance, avoids ECS cost for orchestration~~ **Superseded v5.0** |
| Lambda + Step Functions | Replaces n8n | Eliminates on-prem dependency, all infra in AWS, native error handling/retry, per-step scaling, no n8n licensing concerns |
| EventBridge trigger | Decoupled event bus | FastAPI doesn't need to know about Step Functions; enables future event consumers (notifications, audit) without API changes |
| One Lambda per eval step | 5 separate functions | Independent deploys, scaling, and timeout tuning per step; clear ownership and debugging |
| Python 3.12 for Lambdas | Same as backend | Share prompt templates, models, and DB access patterns; single-language codebase |
| Lambda writes to DB directly | No callback webhook | Removes round-trip to FastAPI; Lambdas are VPC-attached with RDS access; simpler data flow |
| API on ECS Fargate | Managed containers | Scales, no server management, stays in AWS ecosystem |
| SPA on S3 + CF | Static hosting | Cheap, fast, standard for SPAs |
| Google OAuth | Corporate IdP | Already using Google Workspace |
| Barley + manual transcript fallback | Both S3 sync and manual upload supported | Barley sync is primary path but manual upload ensures POC works independently of Barley team timeline |
| Lever deferred | Future phase, not POC | Reduces external dependencies; POC validates AI evaluation value before integration work |
| Slack bot removed | SPA replaces it | Single upload path simplifies architecture |
| S3 watched folder removed | API writes to S3 | Upload triggered by API, not by file appearance |

---

## 9. Future: AI Candidate Analyst (Chat)

_Planned addition — conversational AI assistant for recruiters, powered by Claude Agent SDK._

```
┌─────────────────┐     WebSocket/SSE      ┌──────────────────┐
│  React SPA      │◄─────────────────────►  │  FastAPI (ECS)   │
│  Chat Widget    │                         │  /api/chat/*     │
└─────────────────┘                         └────────┬─────────┘
                                                     │
                                            ┌────────┴─────────┐
                                            │  Agent SDK       │
                                            │  (ECS Fargate)   │
                                            │                  │
                                            │  MCP Tools:      │
                                            │  - query_evals   │
                                            │  - get_cv_text   │
                                            │  - get_transcript │
                                            │  - search_cands  │
                                            │  - get_position  │
                                            └───┬────┬────┬────┘
                                                │    │    │
                                       ┌────────┘    │    └────────┐
                                       ▼             ▼             ▼
                                  ┌─────────┐  ┌─────────┐  ┌──────────┐
                                  │   RDS   │  │   S3    │  │ Bedrock  │
                                  │Postgres │  │ (files) │  │ (Claude) │
                                  └─────────┘  └─────────┘  └──────────┘
```

- **Hosting:** ECS Fargate (long-running container) — Agent SDK requires persistent processes for session management and multi-turn agentic loops
- **Protocol:** WebSocket or SSE for streaming responses to the SPA chat widget
- **Session persistence:** Agent SDK `session_id` allows recruiters to leave and resume conversations
- **Not Lambda-compatible:** Agent SDK's agentic loop (perceive → decide → execute tools → observe → repeat) requires long-running processes, unlike the pipeline's single-shot Bedrock calls

---

## Unresolved Questions

1. ~~**On-prem → AWS networking:**~~ **Resolved (v5.0).** No longer relevant — n8n replaced by Lambda + Step Functions, all within AWS.
2. ~~**n8n licensing:**~~ **Resolved (v5.0).** No longer relevant — n8n removed from architecture.
3. **Barley S3 access pattern:** How will our system read from Barley's S3 bucket — cross-account IAM role, Barley pushes to our bucket, or shared bucket? (Confirm with Barley team)
4. ~~**Lever feedback form API:**~~ **Resolved.** Yes — `GET /feedback_templates/:id` reads form schemas, `POST /opportunities/:id/feedback` submits completed forms. Requires `feedback:write:admin` scope and `perform_as` user ID. Rate limit: 10 req/sec. See `context/spec/003-lever-api-research/functional-spec.md` §3.4.
5. **Lambda cold starts:** Will cold start latency be acceptable for user-triggered evaluations? May need provisioned concurrency if recruiters expect near-instant response. (Monitor after initial deploy)
6. **Lambda VPC NAT Gateway:** Lambdas in VPC need NAT Gateway to reach Bedrock (public endpoint). Confirm NAT Gateway is provisioned in the VPC or consider VPC endpoints for Bedrock.
7. **Shared Lambda layer packaging:** How to structure the shared Python layer (DB access, Bedrock client, prompt utils) — monorepo package or separate build artifact?
