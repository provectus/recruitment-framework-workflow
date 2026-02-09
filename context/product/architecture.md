# System Architecture Overview: Recruitment Workflow POC

- **Version:** 2.0
- **Status:** Revised

---

## 1. Application & Technology Stack

- **Frontend:** React + TypeScript SPA (Vite) — recruiter-facing UI for transcript/CV upload and candidate tracking
- **Backend API:** Python + FastAPI — API layer between SPA, n8n, and external services
- **Workflow Engine:** n8n (self-hosted on-prem, Docker Compose on dedicated instance)
- **Authentication:** Google OAuth 2.0 (corporate Google Workspace)

---

## 2. External Services & APIs

- **ATS (Applicant Tracking):** Lever API — pull candidate data, push evaluation notes back
- **Interview Transcription:** Metaview (manual export — recruiter uploads transcript via SPA)
- **AI Engine:** Claude via Amazon Bedrock — CV analysis, transcript processing, rubric evaluation, feedback generation
- **Identity Provider:** Google Workspace (OAuth 2.0)

---

## 3. Data & Persistence

- **Primary Database:** PostgreSQL (AWS RDS) — evaluations, candidates, artifacts, users, audit trail
- **File Storage:** AWS S3 — uploaded transcripts and CVs (written by API, not a watched folder)
- **Prompt Templates & Rubrics:** Version-controlled files in repository
- **Candidate Source of Truth:** Lever (synced, not duplicated)

**Data Model:**
```
User (1) → Uploads (many)
Position (1) → Candidates (many)
Candidate (1) → Artifacts (many)
  - CV upload + analysis result
  - Screening transcript + summary
  - Technical transcript + evaluation
  - Final recommendation
  - Feedback draft
Evaluation (1) → Audit Log (many)
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
┌─────────────┐     ┌──────────────────────────────────────────┐
│  On-Prem     │     │  AWS Cloud (us-east-1)                   │
│              │     │                                          │
│  ┌────────┐  │     │  ┌──────────┐   ┌─────────────────────┐ │
│  │  n8n   │◄─┼─────┼─►│ FastAPI  │◄──│ React SPA           │ │
│  │(Docker)│  │https │  │(ECS)    │   │(S3 + CloudFront)    │ │
│  └───┬────┘  │     │  └────┬─────┘   └─────────────────────┘ │
│      │       │     │       │                                  │
└──────┼───────┘     │  ┌────┴─────┐  ┌──────┐  ┌───────────┐ │
       │             │  │ RDS      │  │  S3   │  │ Bedrock   │ │
       │             │  │ Postgres │  │(files)│  │ (Claude)  │ │
       └─────────────┼─►└──────────┘  └──────┘  └───────────┘ │
        (Bedrock)    └──────────────────────────────────────────┘
```

**Request flow:**
1. Recruiter logs into SPA via Google OAuth
2. Selects candidate/position (data synced from Lever)
3. Uploads transcript or CV via SPA → FastAPI → S3
4. FastAPI creates evaluation record in Postgres
5. FastAPI triggers n8n workflow via webhook
6. n8n orchestrates: calls Bedrock (Claude), applies rubric, generates evaluation
7. n8n posts results back to FastAPI
8. FastAPI stores results in Postgres, updates Lever
9. SPA polls for updates — recruiter sees evaluation results

---

## 6. n8n Workflows

| Workflow | Trigger | Description |
|----------|---------|-------------|
| `cv-analysis` | API webhook | Parse CV against role requirements via Claude |
| `screening-eval` | API webhook | Process screening transcript, generate summary |
| `technical-eval` | API webhook | Evaluate technical interview against rubric |
| `recommendation` | API webhook | Aggregate scores, generate hire/no-hire recommendation |
| `lever-sync` | API webhook | Push evaluation notes back to Lever candidate profile |
| `feedback-gen` | API webhook | Generate candidate-facing rejection feedback |

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
| SPA instead of Slack-only | React + TS | Recruiters need upload UX + candidate tracking (Metaview-like) |
| Python backend | FastAPI | Team preference, async support, good typing, fast dev |
| n8n on-prem | Docker Compose | Purchased instance, avoids ECS cost for orchestration |
| API on ECS Fargate | Managed containers | Scales, no server management, stays in AWS ecosystem |
| SPA on S3 + CF | Static hosting | Cheap, fast, standard for SPAs |
| Google OAuth | Corporate IdP | Already using Google Workspace |
| Slack bot removed | SPA replaces it | Single upload path simplifies architecture |
| S3 watched folder removed | API writes to S3 | Upload triggered by API, not by file appearance |

---

## Unresolved Questions

1. **On-prem → AWS networking:** Does the n8n instance have direct outbound internet, or do we need VPN/Direct Connect to reach AWS? (Confirm with ops)
2. **n8n licensing:** Self-hosted free tier sufficient for webhook-triggered workflows?
3. **Metaview export format:** What's the exact transcript structure recruiters will upload?
