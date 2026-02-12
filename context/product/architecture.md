# System Architecture Overview: Recruitment Workflow POC

- **Version:** 4.0
- **Status:** Revised — manual-first POC, Lever deferred

---

## 1. Application & Technology Stack

- **Frontend:** React + TypeScript SPA (Vite) — recruiter-facing UI for candidate/position management, transcript/CV upload, and evaluation tracking
- **Backend API:** Python + FastAPI — API layer between SPA, n8n, and external services
- **Workflow Engine:** n8n (self-hosted on-prem, Docker Compose on dedicated instance)
- **Authentication:** Google OAuth 2.0 (corporate Google Workspace)

---

## 2. External Services & APIs

- **Interview Recordings & Transcripts:** Barley — sync recordings and transcripts from Barley's S3 storage, filtered to recruitment interviews only (access pattern TBD)
- **AI Engine:** Claude via Amazon Bedrock — CV analysis, transcript processing, rubric evaluation, feedback generation
- **Identity Provider:** Google Workspace (OAuth 2.0)

**Future (deferred):**
- **ATS (Applicant Tracking):** Lever API — pull candidate data + feedback form schemas, push evaluation notes + approved feedback forms back. Timing depends on POC results and Lever access readiness.

---

## 3. Data & Persistence

- **Primary Database:** PostgreSQL (AWS RDS) — candidates, positions, evaluations, artifacts, users, audit trail
- **File Storage:** AWS S3 — uploaded transcripts, recordings, and CVs (written by API, presigned URLs for upload/download)
- **Prompt Templates & Rubrics:** Version-controlled files in repository
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

### On-Prem (dedicated instance)
- **n8n:** Docker Compose (n8n + its own Postgres for workflow state)
- **Connectivity:** Outbound HTTPS to AWS services (TBD: direct internet or VPN/Direct Connect — confirm with ops)

### AWS Cloud
- **Backend API:** ECS Fargate (FastAPI Docker container)
- **Frontend SPA:** S3 + CloudFront (static hosting)
- **Database:** RDS PostgreSQL (private subnet)
- **File Storage:** S3 (private bucket, presigned URLs for upload/download)
- **AI:** Amazon Bedrock (Claude, us-east-1)
- **Region:** us-east-1

---

## 5. Communication Flow

```
                        ┌──────────────┐
                        │  Barley S3   │
                        │ (recordings/ │
                        │ transcripts) │
                        └──────┬───────┘
                               │ sync (access TBD)
┌─────────────┐     ┌─────────┼────────────────────────────────┐
│  On-Prem     │     │  AWS Cloud (us-east-1)                   │
│              │     │         │                                 │
│  ┌────────┐  │     │  ┌──────┴───┐   ┌─────────────────────┐ │
│  │  n8n   │◄─┼─────┼─►│ FastAPI  │◄──│ React SPA           │ │
│  │(Docker)│  │https │  │(ECS)    │   │(S3 + CloudFront)    │ │
│  └───┬────┘  │     │  └────┬─────┘   └─────────────────────┘ │
│      │       │     │       │                                  │
└──────┼───────┘     │  ┌────┴─────┐  ┌──────┐  ┌───────────┐ │
       │             │  │ RDS      │  │  S3   │  │ Bedrock   │ │
       │             │  │ Postgres │  │(files)│  │ (Claude)  │ │
       └─────────────┼─►└──────────┘  └──────┘  └───────────┘ │
        (Bedrock)    │                                         │
                     └─────────────────────────────────────────┘
```

**Request flow (POC):**
1. Recruiter logs into SPA via Google OAuth
2. Creates candidates and positions manually in the SPA
3. Uploads CV via SPA → FastAPI → S3
4. Uploads transcript manually or system syncs from Barley S3
5. FastAPI creates evaluation record in Postgres
6. FastAPI triggers n8n workflow via webhook
7. n8n orchestrates: calls Bedrock (Claude), applies rubric, generates evaluation
8. n8n posts results back to FastAPI
9. FastAPI stores results in Postgres
10. SPA polls for updates — recruiter sees evaluation results

**Future addition (when Lever integrates):**
- FastAPI syncs candidate/position data from Lever instead of manual entry
- Evaluation notes and approved feedback forms pushed back to Lever

---

## 6. n8n Workflows

| Workflow | Trigger | Description |
|----------|---------|-------------|
| `cv-analysis` | API webhook | Parse CV against role requirements via Claude |
| `screening-eval` | API webhook | Process screening transcript, generate summary |
| `technical-eval` | API webhook | Evaluate technical interview against rubric |
| `recommendation` | API webhook | Aggregate scores, generate hire/no-hire recommendation |
| `feedback-gen` | API webhook | Generate candidate-facing rejection feedback |

**Future (when Lever integrates):**

| Workflow | Trigger | Description |
|----------|---------|-------------|
| `feedback-form-draft` | API webhook | Pull Lever form schema, draft form responses via Claude from transcript |
| `lever-sync` | API webhook | Push evaluation notes + approved feedback forms back to Lever |

---

## 7. Observability & Monitoring

- **API Logging:** CloudWatch Logs (FastAPI container logs)
- **Metrics/Alerts:** CloudWatch Metrics (API health, error rates, latency)
- **Workflow Debugging:** n8n built-in execution history (on-prem)
- **Tracing:** Request IDs passed from SPA → API → n8n → back

---

## 8. Key Architectural Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Manual-first POC | Manual candidate/position/transcript entry | Decouples POC from Lever timeline; proves evaluation pipeline independently |
| SPA instead of Slack-only | React + TS | Recruiters need upload UX + candidate management + evaluation tracking |
| Python backend | FastAPI | Team preference, async support, good typing, fast dev |
| n8n on-prem | Docker Compose | Purchased instance, avoids ECS cost for orchestration |
| API on ECS Fargate | Managed containers | Scales, no server management, stays in AWS ecosystem |
| SPA on S3 + CF | Static hosting | Cheap, fast, standard for SPAs |
| Google OAuth | Corporate IdP | Already using Google Workspace |
| Barley + manual transcript fallback | Both S3 sync and manual upload supported | Barley sync is primary path but manual upload ensures POC works independently of Barley team timeline |
| Lever deferred | Future phase, not POC | Reduces external dependencies; POC validates AI evaluation value before integration work |
| Slack bot removed | SPA replaces it | Single upload path simplifies architecture |
| S3 watched folder removed | API writes to S3 | Upload triggered by API, not by file appearance |

---

## Unresolved Questions

1. **On-prem → AWS networking:** Does the n8n instance have direct outbound internet, or do we need VPN/Direct Connect to reach AWS? (Confirm with ops)
2. **n8n licensing:** Self-hosted free tier sufficient for webhook-triggered workflows?
3. **Barley S3 access pattern:** How will our system read from Barley's S3 bucket — cross-account IAM role, Barley pushes to our bucket, or shared bucket? (Confirm with Barley team)
4. ~~**Lever feedback form API:**~~ **Resolved.** Yes — `GET /feedback_templates/:id` reads form schemas, `POST /opportunities/:id/feedback` submits completed forms. Requires `feedback:write:admin` scope and `perform_as` user ID. Rate limit: 10 req/sec. See `context/spec/003-lever-api-research/functional-spec.md` §3.4.
