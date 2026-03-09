# Functional Specification: Lever API Research

- **Roadmap Item:** Phase 1 → Lever API Research (API Exploration, Integration Strategy, Feedback Form Endpoints)
- **Status:** Completed
- **Author:** Nail (AI-assisted)

---

## 1. Overview and Rationale (The "Why")

Lever is the source of truth for candidates, positions, feedback forms, and interview data at Provectus. Every downstream Tap feature — candidate list, CV analysis, feedback drafting, evaluation pipeline — depends on reading from and writing to Lever.

**Problem:** Without understanding Lever's API capabilities, auth model, rate limits, data schemas, and webhook support, the team cannot design the integration layer or estimate implementation scope.

**Desired outcome:** A complete reference document covering every Lever API endpoint Tap needs, authentication options, sync strategies, and data models — sufficient to unblock implementation planning for Lever Integration (Read) and Lever Integration (Write).

**Success criteria:**
- All API endpoints needed for Phase 1–3 are identified and documented
- Authentication approach is recommended with tradeoffs
- Feedback form read/write capability is confirmed (critical open question from architecture doc)
- Sync strategy is defined (polling vs webhooks per data type)
- Unresolved questions are clearly listed for stakeholder resolution

---

## 2. API Fundamentals

### 2.1 Authentication

Two methods available — choice depends on integration type:

| Method | Use Case | Setup |
|--------|----------|-------|
| **API Key** (Basic Auth) | Internal/customer workflows | Settings → Integrations & API → API Credentials tab. Key = username, password blank. Requires Super Admin. |
| **OAuth 2.0** | Partner/product integrations | Must register app with Lever (name, description, callback URI, logo, scopes). Required for partner program. |

**OAuth 2.0 flow:**
- Auth URL: `https://auth.lever.co/authorize`
- Grant type: Authorization Code
- Include `offline_access` scope for refresh tokens
- Access tokens expire → use refresh token to rotate (no re-auth needed)
- Sandbox: separate app registration, uses `https://api.sandbox.lever.co/v1`

**Recommendation for Tap:** Start with **API Key** for internal tooling (simpler, faster). Migrate to OAuth if Lever restricts any required endpoints to OAuth-only or if we productize.

### 2.2 Environments

| Env | API Base | Auth Server |
|-----|----------|-------------|
| Production | `https://api.lever.co/v1` | `https://auth.lever.co` |
| Sandbox | `https://api.sandbox.lever.co/v1` | Sandbox auth server |

### 2.3 Rate Limits

- **10 req/sec** steady state per API key
- Bursts up to **20 req/sec**
- Postings API: **2 POST req/sec** (applications)
- HTTP 429 on exceed → must implement backoff

### 2.4 Pagination

- Cursor-based: response includes `next` offset token
- Pass `offset` param for subsequent pages
- No arbitrary page jumps — sequential only

### 2.5 Data Format

- JSON over HTTPS only (no HTTP)
- UTF-8 encoding
- `expand=` query param to inline nested objects (user, stage, posting, etc.)

---

## 3. Integration Points by Feature

### 3.1 Candidate & Opportunity Data (Phase 1 — Read)

**Endpoints:**

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/opportunities` | List all pipeline opportunities (with filtering) |
| `GET` | `/opportunities/:id` | Single opportunity detail |
| `GET` | `/opportunities/:id/resumes` | List resumes |
| `GET` | `/opportunities/:id/resumes/:id/download` | Download resume file |
| `GET` | `/opportunities/:id/applications` | List applications |
| `GET` | `/contacts/:id` | Contact details (name, email, phones, location) |

**Key data on Opportunity:**
- `name`, `headline`, `emails`, `phones`, `links`, `location`
- `stageId` + `stageChanges[]` (full history)
- `origin` (agency/applied/internal/referred/sourced/university)
- `sources[]`, `tags[]`
- `ownerId`, `followerIds`
- `applicationIds`, `postingIds`
- `archived` (status + reason)
- `createdAt`, `updatedAt`, `lastInteractionAt`, `lastAdvancedAt`

**Resume parsed data includes:**
- `positions[]` — work history (company, title, dates)
- `schools[]` — education (school, degree, field, dates)

### 3.2 Job Postings & Requirements (Phase 1 — Read)

**Endpoints:**

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/postings` | List all postings |
| `GET` | `/postings/:id` | Single posting detail |
| `GET` | `/postings/:id/apply` | Application form questions |

**Posting data:**
- `text` (job title), `state` (published/internal/closed/draft/pending/rejected)
- `categories` — team, department, location, allLocations, commitment (Full-time/Part-time/Internship), level
- `content` — description (plain + HTML), lists (requirements/responsibilities sections), closing
- `hiringManagerId`, `ownerId`, `followerIds`
- `requisitionCodes[]`, `workplaceType` (onsite/remote/hybrid)

### 3.3 Pipeline Stages (Phase 1 — Read)

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/stages` | List all pipeline stages |
| `GET` | `/stages/:id` | Single stage |

Model: `{ id, text }` — simple ID + label.

### 3.4 Feedback Forms (Phase 2/3 — Read + Write)

This is the **critical integration point** for Tap's evaluation pipeline. Lever API supports both reading form schemas and submitting completed forms programmatically — confirmed.

**Read:**

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/opportunities/:id/feedback` | List all feedback for opportunity |
| `GET` | `/opportunities/:id/feedback/:id` | Single feedback form |
| `GET` | `/feedback_templates` | List all feedback templates |
| `GET` | `/feedback_templates/:id` | Single template |

**Write:**

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/opportunities/:id/feedback` | Create feedback form |
| `PUT` | `/opportunities/:id/feedback/:id` | Update existing feedback |
| `POST` | `/feedback_templates` | Create feedback templates |
| `DELETE` | `/feedback_templates/:id` | Delete templates |

**`POST /opportunities/:id/feedback` params:**
- Required: `baseTemplateId`, `perform_as` (user ID)
- Optional: `panelId`, `interviewId`, field values, timestamps

**Feedback field types:**
`code`, `date`, `dropdown`, `multiple choice`, `multiple select`, `score system`, `score` (thumbs up/down), `scorecard` (multi-skill eval), `text`, `textarea`, `yes/no`

**Field structure:**
```json
{
  "id": "field-uid",
  "type": "score",
  "text": "Overall recommendation",
  "description": "...",
  "required": true,
  "value": "4 - Strong Hire",
  "prompt": "...",
  "options": ["4 - Strong Hire", "3 - Hire", "2 - No Hire", "1 - Strong No Hire"]
}
```

### 3.5 Interviews (Phase 2 — Read + Write)

**Read:**

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/opportunities/:id/interviews` | List interviews for opportunity |

Interview includes: `subject`, `interviewers[]`, `date`, `duration`, `location`, `feedbackTemplateId`, `feedbackFormIds[]`, `stageId`.

**Write:**

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/opportunities/:id/interviews` | Schedule interview |
| `PUT` | `/opportunities/:id/interviews/:id` | Update interview |

**Interviewer model:** `{ id, name, email }` — maps to Lever Users.

### 3.6 Notes & Files (Phase 2 — Write)

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/opportunities/:id/notes` | Add notes (evaluation summaries) |
| `POST` | `/opportunities/:id/files` | Upload files (30MB max) |
| `POST` | `/opportunities/:id/addTags` | Add tags |
| `POST` | `/opportunities/:id/addLinks` | Add links |

### 3.7 Stage Management (Phase 2 — Write)

| Method | Path | Purpose |
|--------|------|---------|
| `PUT` | `/opportunities/:id/stage` | Change opportunity stage |
| `PUT` | `/opportunities/:id/archived` | Archive/unarchive |

### 3.8 Webhooks (Event-Driven Sync)

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/webhooks` | Create webhook subscription |

**Available events:**
- `applicationCreated`
- `candidateStageChange` (critical for pipeline tracking)
- `candidateArchiveChange`
- `candidateHired`
- `candidateDeleted`
- `interviewCreated` / `interviewUpdated` / `interviewDeleted`

**Webhook behavior:**
- Must return 2xx to acknowledge
- 5 retries with exponential backoff on failure
- History: last 1,000 requests from past 2 weeks
- Signature tokens per event type for verification
- Testing: use ngrok for local dev; test button available in admin UI

### 3.9 Users & Admin (Reference Data)

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/users/:id` | User detail (name, email, role, jobTitle, managerId) |

Access roles: `super admin`, `admin`, `team member`, `limited team member`, `interviewer`.

---

## 4. OAuth Scopes Required for Tap

Based on feature needs across all phases:

| Scope | Phase |
|-------|-------|
| `opportunities:read:admin` + `opportunities:write:admin` | 1 (read), 2 (write) |
| `feedback:read:admin` + `feedback:write:admin` | 2 |
| `feedback_templates:read:admin` | 2 |
| `postings:read:admin` | 1 |
| `stages:read:admin` | 1 |
| `interviews:read:admin` + `interviews:write:admin` | 2 |
| `notes:write:admin` | 2 |
| `files:write:admin` | 2 |
| `resumes:read:admin` | 1 |
| `tags:read:admin` | 1 |
| `webhooks:write:admin` | 1 |
| `users:read:admin` | 1 |
| `offline_access` | All (refresh tokens) |

Write scopes include all corresponding read permissions.

---

## 5. Scope and Boundaries

### In-Scope (this spec)
- Lever API authentication model and recommendation
- All endpoint documentation needed for Phase 1–3
- Feedback form read/write confirmation
- Webhook event catalog
- OAuth scope requirements
- Sync strategy recommendations
- Rate limit and pagination details

### Out-of-Scope
- Implementation code (covered in Lever Integration Read/Write specs)
- n8n workflow design for Lever sync (separate spec)
- Barley integration (separate spec)
- Database schema for cached Lever data (Lever Integration Read spec)

---

## 6. Unresolved Questions

1. **API Key vs OAuth** — API keys are for "internal workflows." Does Lever restrict any endpoints (especially feedback write) to OAuth-only? Need to verify with Lever docs or by testing in sandbox.
2. **Sandbox access** — Do we already have a Lever sandbox account, or do we need to request one?
3. **Feedback form `perform_as`** — The `POST /feedback` endpoint requires a `perform_as` user ID. Options: (a) use a service account, (b) map to the actual interviewer's Lever user ID.
4. **Rate limit sufficiency** — 10 req/sec should be fine for our scale, but worth confirming typical batch sizes for initial sync.
5. **EU data residency** — Lever has EU endpoints (`api.eu.lever.co`). Is our Lever instance US or EU?

---

## Sources

- [Lever API Overview](https://hire.lever.co/developer/documentation)
- [Lever OAuth Documentation](https://hire.lever.co/developer/oauth)
- [Lever Postings API (GitHub)](https://github.com/lever/postings-api)
- [Lever API Directory (GetKnit)](https://www.getknit.dev/blog/lever-api-directory)
- [Lever API Go Data Models](https://pkg.go.dev/github.com/corbaltcode/lever-data-api-go/model)
- [Lever Webhook Events (GetKnit)](https://developers.getknit.dev/docs/lever-real-time-events)
- [Lever API Updates](https://hire.lever.co/developer/updates)
- [Lever Help Center — API Credentials](https://help.lever.co/hc/en-us/articles/20087297592477-Generating-and-using-API-credentials)
- [Lever Help Center — Feedback Forms](https://help.lever.co/hc/en-us/articles/20087332875165-Creating-Interview-Feedback-Forms)
