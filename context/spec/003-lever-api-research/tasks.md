# Tasks: Lever API Integration

---

## Slice 0: Prerequisites & configuration

Lever API key obtained, config wired, sandbox access confirmed. Team can make authenticated API calls.

- [ ] Obtain Lever API key from admin (Settings → Integrations & API → API Credentials) **[Manual]**
- [ ] Confirm Lever instance region (US vs EU) — determines base URL **[Manual]**
- [ ] Request Lever sandbox account for development/testing (if not already available) **[Manual]**
- [ ] Add Lever config to `app/config.py`: `LEVER_API_KEY`, `LEVER_BASE_URL`, `LEVER_WEBHOOK_SECRET` **[Agent: python-architect]**
- [ ] Update `.env.example` with Lever env vars **[Agent: python-architect]**
- [ ] **Verify:** `curl -u $LEVER_API_KEY: https://api.lever.co/v1/stages` returns 200 with stage list

---

## Slice 1: Lever API client foundation

Reusable async HTTP client with auth, rate limiting, pagination, and error handling.

- [ ] Create `app/services/lever/client.py`: `LeverClient` class wrapping `httpx.AsyncClient` with Basic Auth header injection **[Agent: python-architect]**
- [ ] Implement rate limiter (8 req/sec with burst headroom) in `client.py` **[Agent: python-architect]**
- [ ] Implement cursor-based pagination helper **[Agent: python-architect]**
- [ ] Implement retry logic with exponential backoff for 429 and 5xx **[Agent: python-architect]**
- [ ] Create `app/services/lever/models.py`: Pydantic models for core Lever types (Opportunity, Posting, Stage, User, FeedbackTemplate, FeedbackField) **[Agent: python-architect]**
- [ ] Create `app/services/lever/exceptions.py`: `LeverAuthError`, `LeverValidationError`, `LeverServerError`, `LeverRateLimitError` **[Agent: python-architect]**
- [ ] Register `LeverClient` in FastAPI lifespan (create on startup, close on shutdown) **[Agent: python-architect]**
- [ ] Tests: auth header correctness, rate limiter throttling, pagination with mock multi-page responses, retry on 429/5xx, error mapping **[Agent: python-architect]**
- [ ] **Verify:** Client instantiates, authenticates, and fetches `/stages` from sandbox or production

---

## Slice 2: Read endpoints — Stages, Users, Postings (reference data)

Cached reference data available to the rest of the app. Low-change-frequency data fetched and stored locally.

- [ ] Create `app/services/lever/stages.py`: `list_stages()` **[Agent: python-architect]**
- [ ] Create `app/services/lever/users.py`: `list_users()`, `get_user()` **[Agent: python-architect]**
- [ ] Create `app/services/lever/postings.py`: `list_postings()`, `get_posting()` **[Agent: python-architect]**
- [ ] DB models for cached stages, users, postings (with `lever_*` external IDs) + Alembic migrations **[Agent: python-architect]**
- [ ] Sync service: fetch from Lever → upsert into local DB **[Agent: python-architect]**
- [ ] Tests: mock API responses → correct Pydantic parsing → correct DB records **[Agent: python-architect]**
- [ ] **Verify:** Run sync → stages, users, postings appear in local DB with correct data

---

## Slice 3: Read endpoints — Opportunities & Candidates

Core candidate data synced from Lever. Opportunity data mapped to Tap's candidate model.

- [ ] Create `app/services/lever/opportunities.py`: `list_opportunities()`, `get_opportunity()`, `get_resumes()`, `download_resume()` **[Agent: python-architect]**
- [ ] DB models for candidates (mapped from Lever opportunities) + Alembic migration **[Agent: python-architect]**
- [ ] Data mapping layer: Lever Opportunity → Tap Candidate (see technical-considerations.md §4) **[Agent: python-architect]**
- [ ] Sync service: paginated fetch of all active opportunities → upsert candidates **[Agent: python-architect]**
- [ ] API endpoint: `GET /candidates` (with pagination, filtering by stage/posting) **[Agent: python-architect]**
- [ ] API endpoint: `GET /candidates/:id` (with Lever data + local evaluation status) **[Agent: python-architect]**
- [ ] Tests: opportunity mapping, paginated sync, candidate API endpoints **[Agent: python-architect]**
- [ ] **Verify:** Sync pulls real candidates from Lever → visible via `/candidates` API

---

## Slice 4: Feedback templates (Read)

Feedback form schemas available for AI draft generation.

- [ ] Create `app/services/lever/feedback.py`: `list_feedback_templates()`, `get_feedback_template()`, `list_opportunity_feedback()` **[Agent: python-architect]**
- [ ] DB model for `FeedbackFormTemplate` (template ID, name, fields JSON, associated posting/stage) + migration **[Agent: python-architect]**
- [ ] On-demand fetch with caching: check local DB first, fetch from Lever if stale (1h TTL) **[Agent: python-architect]**
- [ ] API endpoint: `GET /feedback-templates` and `GET /feedback-templates/:id` **[Agent: python-architect]**
- [ ] Tests: template fetch, caching behavior, field type parsing **[Agent: python-architect]**
- [ ] **Verify:** Fetch feedback template from Lever → fields parsed correctly → cached locally

---

## Slice 5: Webhooks (event-driven sync)

Real-time updates from Lever via webhooks. FastAPI receives, verifies, and processes events.

- [ ] Create `app/routers/webhooks.py`: `POST /webhooks/lever/:event_type` **[Agent: python-architect]**
- [ ] Webhook signature verification middleware **[Agent: python-architect]**
- [ ] Event handlers: `candidateStageChange` → update candidate stage, `interviewCreated/Updated` → update interviews **[Agent: python-architect]**
- [ ] Create `app/services/lever/webhooks.py`: `register_webhook()`, `list_webhooks()` for setup **[Agent: python-architect]**
- [ ] Management command or startup hook to register/verify webhooks **[Agent: python-architect]**
- [ ] Tests: signature verification, event parsing, idempotent processing, handler routing **[Agent: python-architect]**
- [ ] **Verify:** Trigger test webhook from Lever admin → FastAPI receives and processes → local DB updated

---

## Slice 6: Feedback form write (Phase 2)

Submit AI-drafted, reviewer-approved feedback forms back to Lever.

- [ ] Create `app/services/lever/feedback.py`: `create_feedback()`, `update_feedback()` **[Agent: python-architect]**
- [ ] DB model for `FeedbackFormDraft` (draft status: draft/approved/submitted/failed, field values, linked template + opportunity) + migration **[Agent: python-architect]**
- [ ] Lever user mapping: resolve Tap user → Lever user ID by email for `perform_as` **[Agent: python-architect]**
- [ ] API endpoint: `POST /candidates/:id/feedback/:draft_id/submit` → validate → submit to Lever **[Agent: python-architect]**
- [ ] Field value validation against template schema before submission **[Agent: python-architect]**
- [ ] Tests: create feedback with mock Lever response, user mapping, field validation, error handling **[Agent: python-architect]**
- [ ] **Verify:** Submit feedback form via API → appears in Lever opportunity's feedback tab

---

## Slice 7: Notes & stage management write (Phase 2)

Push evaluation summaries and stage transitions back to Lever.

- [ ] Add to `app/services/lever/opportunities.py`: `add_note()`, `add_tags()`, `change_stage()`, `upload_file()` **[Agent: python-architect]**
- [ ] API endpoints for triggering Lever writes from evaluation results **[Agent: python-architect]**
- [ ] Tests: note creation, tag addition, stage change **[Agent: python-architect]**
- [ ] **Verify:** Add note via API → appears on Lever opportunity

---

## Dependencies

```
Slice 0 → Slice 1 → Slice 2 → Slice 3
                  ↘ Slice 4
                  ↘ Slice 5
                        Slice 4 → Slice 6
                        Slice 3 → Slice 7
```

---

## Recommendations

| Area | Recommendation |
|------|----------------|
| Auth method | Start with API Key. Test feedback write endpoints in sandbox — if restricted to OAuth, pivot early. |
| `perform_as` | Map by email. Require Lever user cache (Slice 2) before feedback write (Slice 6). |
| Rate limits | 8 req/sec self-throttle is conservative enough. Monitor 429 rate in CloudWatch. |
| Webhook reliability | Always pair webhooks with periodic polling as fallback. Never rely on webhooks alone. |
| Testing | Lever sandbox is essential for integration tests. Prioritize obtaining sandbox access in Slice 0. |
| Pydantic models | Use `model_config = {"extra": "ignore"}` to tolerate Lever adding new fields without breaking. |
