# Technical Considerations: Lever API Integration

- **Functional Specification:** `context/spec/003-lever-api-research/functional-spec.md`
- **Status:** Completed
- **Author(s):** Nail (AI-assisted)

---

## 1. Authentication Architecture

### Recommended Approach: API Key (Phase 1), OAuth migration path (future)

API Key auth for internal tooling is the fastest path. The key is passed as Basic Auth username with an empty password.

```python
import httpx
import base64

LEVER_API_KEY = settings.lever_api_key
LEVER_BASE_URL = "https://api.lever.co/v1"

headers = {
    "Authorization": f"Basic {base64.b64encode(f'{LEVER_API_KEY}:'.encode()).decode()}"
}
```

**If OAuth is needed later**, the backend already has the OAuth pattern from Cognito auth. The Lever OAuth flow would be:
1. Register app with Lever (admin UI)
2. Add `/lever/auth/callback` route to FastAPI
3. Store access + refresh tokens in DB (per-tenant if multi-org)
4. Token refresh middleware before API calls

### Configuration

New env vars for `app/config.py`:

| Variable | Purpose | Example |
|----------|---------|---------|
| `LEVER_API_KEY` | API key for Basic Auth | `your_lever_api_key_here` |
| `LEVER_BASE_URL` | API base URL | `https://api.lever.co/v1` |
| `LEVER_WEBHOOK_SECRET` | Webhook signature verification | `whsec_...` |
| `LEVER_EU_REGION` | Whether to use EU endpoint | `false` |

---

## 2. Client Architecture

### Lever API Client

A single `LeverClient` class wrapping `httpx.AsyncClient` with built-in auth, rate limiting, pagination, and error handling.

```
app/services/lever/
  __init__.py
  client.py          # LeverClient — HTTP layer with auth, retries, rate limiting
  opportunities.py   # Opportunity-specific operations
  postings.py        # Posting/job operations
  feedback.py        # Feedback form read/write
  stages.py          # Stage lookups
  webhooks.py        # Webhook management
  models.py          # Pydantic models for Lever API responses
```

**Design decisions:**
- **Async httpx** — consistent with the rest of the backend (async everywhere)
- **Thin service wrappers** — each module exposes domain methods (`list_opportunities()`, `create_feedback()`), delegates HTTP to `LeverClient`
- **Pydantic models for responses** — type-safe parsing, validation, and IDE support
- **Singleton client per app lifetime** — created in FastAPI lifespan, shared via dependency injection

### Rate Limiting

Lever enforces 10 req/sec with bursts to 20. The client must self-throttle:

```python
import asyncio
from collections import deque
from time import monotonic

class RateLimiter:
    def __init__(self, max_per_second: int = 8):  # leave headroom below 10
        self.max_per_second = max_per_second
        self.timestamps: deque[float] = deque()

    async def acquire(self):
        now = monotonic()
        while self.timestamps and now - self.timestamps[0] > 1.0:
            self.timestamps.popleft()
        if len(self.timestamps) >= self.max_per_second:
            sleep_time = 1.0 - (now - self.timestamps[0])
            await asyncio.sleep(sleep_time)
        self.timestamps.append(monotonic())
```

- Target 8 req/sec to leave 20% headroom
- On HTTP 429: exponential backoff (1s, 2s, 4s) with max 3 retries
- Log rate limit hits as warnings

### Pagination Helper

Lever uses cursor-based pagination. Generic helper:

```python
async def paginate(client: LeverClient, path: str, params: dict | None = None) -> list[dict]:
    results = []
    offset = None
    while True:
        query = {**(params or {})}
        if offset:
            query["offset"] = offset
        response = await client.get(path, params=query)
        data = response.json()
        results.extend(data.get("data", []))
        if not data.get("hasNext"):
            break
        offset = data.get("next")
    return results
```

### Error Handling

| HTTP Status | Meaning | Action |
|-------------|---------|--------|
| 200 | Success | Process response |
| 400 | Bad request | Log + raise `LeverValidationError` |
| 401 | Auth failure | Log + raise `LeverAuthError` (check API key) |
| 403 | Insufficient scope | Log + raise `LeverAuthError` (check permissions) |
| 404 | Not found | Return `None` (expected for deleted resources) |
| 429 | Rate limited | Backoff + retry (max 3) |
| 5xx | Lever outage | Backoff + retry (max 3), then raise `LeverServerError` |

---

## 3. Data Sync Strategy

### Per-Data-Type Approach

| Data | Strategy | Frequency | Rationale |
|------|----------|-----------|-----------|
| Opportunities | Webhook `candidateStageChange` + periodic poll | Real-time + every 15 min | Real-time stage updates + catch missed events |
| Postings | Periodic poll | Hourly | Low change frequency |
| Feedback templates | On-demand fetch + cache | TTL 1 hour | Rarely change, needed at form fill time |
| Stages | Cache on startup + refresh | Daily | Nearly static |
| Users | Cache on startup + refresh | Daily | Rarely change |
| Interview events | Webhooks | Real-time | Need real-time for scheduling flows |

### Webhook Architecture

```
Lever → HTTPS POST → FastAPI /webhooks/lever/:event_type
                          ↓
                    Verify signature token
                          ↓
                    Parse event payload
                          ↓
                    Update local DB / trigger n8n
                          ↓
                    Return 200
```

**Webhook endpoint requirements:**
- Public HTTPS endpoint (behind ALB)
- Signature verification per event type
- Idempotent processing (Lever may retry)
- Fast response (< 5s) — offload heavy work to background task or n8n
- Store raw webhook payloads for debugging (30-day retention)

**Local development:** Use ngrok or similar tunnel. Lever admin UI has a test button per webhook.

### Initial Sync (Bootstrap)

On first deployment or after data reset:

1. Fetch all stages → cache
2. Fetch all users → cache
3. Fetch all active postings → store
4. Fetch all non-archived opportunities (paginated) → store
5. Register webhooks for ongoing sync

Estimated volume for a ~500-opportunity Lever instance at 10 req/sec:
- Stages: 1 request
- Users: ~5 requests (paginated)
- Postings: ~5 requests
- Opportunities: ~50 requests (500 / default page size)
- **Total: ~60 requests ≈ 8 seconds**

---

## 4. Data Mapping

### Lever Opportunity → Tap Candidate

| Lever Field | Tap Field | Notes |
|-------------|-----------|-------|
| `id` | `lever_opportunity_id` | Primary external key |
| `name` | `full_name` | |
| `headline` | `headline` | Current title/role |
| `emails[0]` | `email` | Primary email |
| `phones[0]` | `phone` | Primary phone |
| `location` | `location` | |
| `stageId` | `current_stage_id` | FK to cached stages |
| `postingIds` | Relationship | Many-to-many via postings |
| `origin` | `source_type` | Enum mapping |
| `sources[]` | `sources` | Array of strings |
| `tags[]` | `tags` | Array of strings |
| `ownerId` | `owner_lever_user_id` | FK to cached users |
| `archived.reason` | `archived_reason` | Null if active |
| `createdAt` | `lever_created_at` | Lever timestamp |
| `updatedAt` | `lever_updated_at` | For sync conflict detection |

### Lever Posting → Tap Position

| Lever Field | Tap Field | Notes |
|-------------|-----------|-------|
| `id` | `lever_posting_id` | Primary external key |
| `text` | `title` | Job title |
| `state` | `status` | Enum: published/internal/closed/draft |
| `categories.team` | `team` | |
| `categories.department` | `department` | |
| `categories.location` | `location` | |
| `categories.commitment` | `commitment` | Full-time/Part-time/etc. |
| `content.description` | `description` | Plain text |
| `content.descriptionHtml` | `description_html` | HTML version |
| `content.lists[]` | `requirements`, `responsibilities` | Parsed from lists |
| `hiringManagerId` | `hiring_manager_lever_id` | FK to cached users |
| `workplaceType` | `workplace_type` | onsite/remote/hybrid |

### Lever Feedback Template → Tap FeedbackFormTemplate

| Lever Field | Tap Field | Notes |
|-------------|-----------|-------|
| `id` | `lever_template_id` | Primary external key |
| `text` | `name` | Template name |
| `fields[]` | `fields` | JSON array of field definitions |
| `fields[].type` | Field type enum | code/date/dropdown/score/scorecard/text/etc. |
| `fields[].required` | Required flag | |
| `fields[].options` | Options array | For dropdown/score/multiple choice |

---

## 5. Feedback Form Write Flow

The most complex integration — here's the full flow:

```
1. Recruiter triggers evaluation in Tap
2. FastAPI fetches feedback template from Lever (GET /feedback_templates/:id)
3. n8n workflow receives template schema + interview transcript
4. Claude (Bedrock) drafts field values matching template structure
5. Draft stored in Tap DB (status: draft)
6. Reviewer sees draft in SPA, edits fields, clicks "Approve"
7. FastAPI calls POST /opportunities/:id/feedback with:
   - baseTemplateId: template ID
   - perform_as: interviewer's Lever user ID
   - field values from approved draft
8. Lever creates the feedback form attributed to the interviewer
9. Tap marks draft as "submitted", stores Lever feedback ID
```

**`perform_as` handling:**
- Map Tap users to Lever users by email
- On Lever user cache, index by email for fast lookup
- If no matching Lever user, fall back to a designated service account (configurable)

---

## 6. Testing Strategy

### API Client Tests
- **Unit:** Mock httpx responses for each endpoint, test pagination, rate limiting, error handling
- **Integration:** Against Lever sandbox (if available) — CRUD cycle for feedback forms
- **Contract tests:** Validate Pydantic models against actual Lever API responses (snapshot tests)

### Sync Tests
- **Unit:** Webhook payload parsing, data mapping functions, conflict detection
- **Integration:** Webhook endpoint receives test payload → DB updated correctly
- **Idempotency:** Same webhook delivered twice → no duplicate records

### Feedback Write Tests
- **Unit:** Template → draft mapping, field value formatting per type
- **Integration:** Full flow: fetch template → generate draft → submit to sandbox
- **Edge cases:** Required field missing, invalid score value, template changed between draft and submit

---

## 7. Risk Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Lever API downtime | Sync stalls, feedback submission fails | Queue writes for retry; cached data serves reads |
| Rate limit exceeded during initial sync | 429 errors, slow bootstrap | Self-throttle at 8 req/sec, paginate efficiently |
| Webhook delivery failure | Missed stage changes | Periodic poll as fallback (every 15 min) |
| API key leaked | Full Lever access compromised | Store in AWS Secrets Manager, rotate periodically |
| Lever schema changes | Pydantic validation errors | Lenient parsing (`model_config = {"extra": "ignore"}`), monitor for new fields |
| `perform_as` user not found | Feedback submission rejected | Validate mapping before submission, fallback to service account |
| EU data residency mismatch | API calls fail or violate compliance | Confirm region early, make base URL configurable |
| Webhook signature bypass | Spoofed events processed | Always verify signature token, reject unsigned requests |
