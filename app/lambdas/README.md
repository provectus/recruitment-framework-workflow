# Evaluation Pipeline: Lambda Functions

## What
Five AWS Lambda functions that evaluate recruitment candidates using Claude AI (via Amazon Bedrock). Each function handles one step of the evaluation — from CV analysis through rejection feedback. Results are structured JSON written directly to RDS Postgres.

## Why
- **Decoupled from API:** Lambdas run asynchronously via EventBridge + Step Functions — the FastAPI backend just publishes events and polls results
- **Independent scaling:** Each step has different compute/time profiles (technical eval with rubrics takes longer than CV parsing)
- **Structured AI outputs:** Every Lambda forces Claude to respond via tool_use with a strict JSON schema, ensuring predictable data in the database
- **Direct DB writes:** Lambdas are VPC-attached and write evaluation results directly to RDS — no callback round-trip to FastAPI

## Where

```
app/lambdas/
├── cv_analysis/
│   └── handler.py          # CV parsing + requirements matching
├── screening_eval/
│   └── handler.py          # Screening interview transcript analysis
├── technical_eval/
│   └── handler.py          # Technical interview scoring against rubric
├── recommendation/
│   └── handler.py          # Hire/no-hire recommendation synthesis
├── feedback_gen/
│   └── handler.py          # Rejection feedback generation
├── shared/
│   ├── bedrock.py           # invoke_claude_structured() — Bedrock client with retry
│   ├── db.py                # get_session() — SQLAlchemy session (SSM/Secrets Manager creds)
│   ├── s3.py                # get_document_text() — PDF/DOCX/text extraction from S3
│   ├── models.py            # SQLAlchemy models (Evaluation, Position, Document, etc.)
│   ├── queries.py           # fetch_latest_completed_result() — cross-step data lookups
│   ├── mock_bedrock.py      # Mock Bedrock responses for testing
│   └── prompts/
│       ├── cv_analysis.py   # System prompt + tool schema for CV analysis
│       ├── screening_eval.py
│       ├── technical_eval.py
│       ├── recommendation.py
│       ├── feedback_gen.py
│       └── formatters.py    # Shared prompt formatting utilities
├── tests/
│   ├── test_cv_analysis_handler.py
│   ├── test_screening_eval_handler.py
│   ├── test_technical_eval_handler.py
│   ├── test_recommendation_handler.py
│   ├── test_feedback_gen_handler.py
│   └── test_shared.py
└── requirements.txt

infra/evaluation_pipeline.tf   # Step Functions state machine + Lambda definitions
```

## Pipeline Flow

**Orchestration:** EventBridge (custom bus) → Step Functions (Standard workflow) → Lambda

**Event-driven dispatch:** FastAPI publishes `evaluation.requested` events with `step_type`. Step Functions Choice state routes to the correct Lambda.

```
                    ┌────────────────────────────────────────────────────────────┐
                    │                   Step Functions                           │
                    │                                                            │
  EventBridge      │   ┌─────────────┐    ┌────────────────┐                   │
  evaluation.      │   │             │    │                │                   │
  requested  ──────┼─► │   Choice    │───►│  cv_analysis   │──► Done           │
                    │   │  (step_type)│    │                │                   │
                    │   │             │───►│ screening_eval │──► Done           │
                    │   │             │    │                │                   │
                    │   │             │───►│ technical_eval │──► recommendation │
                    │   │             │    │                │     │             │
                    │   │             │───►│ recommendation │──► Done           │
                    │   │             │    │                │                   │
                    │   │             │───►│  feedback_gen  │──► Done           │
                    │   └─────────────┘    └────────────────┘                   │
                    │                                                            │
                    │   Retry: 2 attempts, 5s interval, 2x backoff              │
                    │   On failure: Catch → mark evaluation as "failed"          │
                    └────────────────────────────────────────────────────────────┘
```

**Each Lambda follows the same pattern:**
1. Fetch evaluation record from RDS (mark status → `running`)
2. Load relevant data (documents from S3, prior evaluations from RDS)
3. Build prompt with position context + document content
4. Single `invoke_claude_structured()` call to Bedrock (forced tool_use)
5. Validate and post-process the structured response
6. Write result JSON to evaluation record (mark status → `completed`)

## Lambda Details

### cv_analysis
**Input:** `evaluation_id` → fetches CV document from S3, position requirements from RDS
**Output:** `skills_match[]`, `experience_relevance`, `education`, `signals_and_red_flags`, `overall_fit`
**Dependencies:** None (entry point)

### screening_eval
**Input:** `evaluation_id` → fetches screening transcript from S3, position requirements from RDS
**Output:** `key_topics[]`, `strengths[]`, `concerns[]`, `communication_quality`, `motivation_culture_fit`, `requirements_alignment[]`
**Dependencies:** None (entry point)
**Validation:** Transcript must be ≥ 100 words

### technical_eval
**Input:** `evaluation_id` → fetches technical transcript from S3, rubric from RDS, prior CV analysis + screening eval results
**Output:** `criteria_scores[]` (score/weight/evidence per criterion), `weighted_total`, `strengths_summary[]`, `improvement_areas[]`, `cv_alignment`, `screening_consistency`
**Dependencies:** Optionally reads cv_analysis and screening_eval results for cross-signal context

### recommendation
**Input:** `evaluation_id` → fetches all prior evaluation results from RDS
**Output:** `recommendation` (hire/no_hire/needs_discussion), `confidence` (high/medium/low), `reasoning`, `missing_inputs[]`
**Dependencies:** Reads cv_analysis, screening_eval, technical_eval results (all optional — gracefully handles missing steps)

### feedback_gen
**Input:** `evaluation_id` → fetches all prior evaluation results from RDS
**Output:** `feedback_text` (150-350 words), `rejection_stage` (cv_review/screening/technical)
**Dependencies:** Reads available evaluation results to determine rejection stage and tailor feedback

## Shared Utilities

| Module | Purpose |
|--------|---------|
| `bedrock.py` | `invoke_claude_structured()` — forced tool_use Bedrock call with 3x retry on throttle/timeout |
| `db.py` | `get_session()` — SQLAlchemy session using SSM params + Secrets Manager for DB creds |
| `s3.py` | `get_document_text()` — extracts text from PDF (pypdf), DOCX (python-docx), or plaintext |
| `queries.py` | `fetch_latest_completed_result()` — gets latest completed evaluation result by step_type |
| `models.py` | SQLAlchemy models: Evaluation, Position, Document, CandidatePosition, PositionRubricVersion |
| `prompts/*.py` | Per-step system prompts and tool schemas |

## Configuration

| Env Var | Purpose |
|---------|---------|
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USERNAME` | RDS connection (from SSM) |
| `DB_PASSWORD_SECRET_ARN` | Secrets Manager ARN for DB password |
| `S3_BUCKET` | Files bucket name |
| `BEDROCK_MODEL_ID` | Claude model ID (default: claude-3-sonnet) |
| `MOCK_BEDROCK` | Set to `true` for testing with mock responses |
