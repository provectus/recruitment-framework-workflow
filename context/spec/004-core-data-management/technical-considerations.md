# Technical Specification: Core Data Management

- **Functional Specification:** `context/spec/004-core-data-management/functional-spec.md`
- **Status:** Draft
- **Author(s):** Nail

---

## 1. High-Level Technical Approach

This feature adds the foundational CRUD layer for candidates, positions, and teams. It spans both backend and frontend:

- **Backend:** 4 new SQLModel models (Team, Candidate, Position, CandidatePosition), 3 service modules, 3 routers under `/api/`. Establishes new patterns: soft delete (`is_archived`), Python `StrEnum` for status/stage fields, offset/limit pagination, foreign keys, and a many-to-many association table with metadata (pipeline stage). Server-side validation enforces stage transition rules.

- **Frontend:** 5 new routes, 3 feature modules, navigation sidebar, and missing shadcn/ui components + react-hook-form/zod. API client regenerated from OpenAPI spec after backend is built.

- **Migration:** One Alembic migration adding all 4 tables.

---

## 2. Proposed Solution & Implementation Plan

### 2.1 Data Model / Database Changes

**Enums** (Python `StrEnum`, stored as VARCHAR in Postgres):

| Enum | Values |
|------|--------|
| `PositionStatus` | `open`, `on_hold`, `closed` |
| `PipelineStage` | `new`, `screening`, `technical`, `offer`, `hired`, `rejected` |

**Tables:**

| Table | Key Columns | Notes |
|-------|-------------|-------|
| `teams` | `id` PK, `name` (unique, not null), `created_at`, `updated_at`, `is_archived` | Simple lookup table |
| `positions` | `id` PK, `title` (not null), `requirements` (text, nullable), `status` (PositionStatus, default `open`), `team_id` FK→teams, `hiring_manager_id` FK→users, `created_at`, `updated_at`, `is_archived` | |
| `candidates` | `id` PK, `full_name` (not null), `email` (unique, not null), `created_at`, `updated_at`, `is_archived` | |
| `candidate_positions` | `id` PK, `candidate_id` FK→candidates, `position_id` FK→positions, `stage` (PipelineStage, default `new`), `created_at`, `updated_at` | Unique constraint on (`candidate_id`, `position_id`) |

**Relationships:**
- Position → Team (many-to-one)
- Position → User as hiring manager (many-to-one)
- Candidate ↔ Position (many-to-many via `candidate_positions`)

**Soft delete pattern:** `is_archived: bool` column (default `False`) on teams, positions, candidates. All list queries filter `WHERE is_archived = false` by default.

**Files:**
- `app/backend/app/models/team.py`
- `app/backend/app/models/position.py`
- `app/backend/app/models/candidate.py`
- `app/backend/app/models/candidate_position.py`
- `app/backend/app/models/enums.py` — shared StrEnum definitions
- Update `app/backend/app/models/__init__.py` — import all new models

**Migration:** Single Alembic migration `YYYY-MM-DD_add_core_data_tables.py` creating all 4 tables with indexes on FKs and the unique constraint.

### 2.2 API Contracts

All endpoints require authentication (`get_current_user` dependency). Responses use Pydantic schemas separate from DB models.

**Pagination envelope** (used by all list endpoints):

```
{ "items": [...], "total": int, "offset": int, "limit": int }
```

**Query params for lists:** `offset` (default 0), `limit` (default 20, max 100).

#### Teams (`app/backend/app/routers/teams.py`)

| Method | Path | Description | Request Body | Response |
|--------|------|-------------|-------------|----------|
| `GET` | `/api/teams` | List teams (non-archived) | — | `TeamResponse[]` |
| `POST` | `/api/teams` | Create team | `{ name: str }` | `TeamResponse` (201) |
| `DELETE` | `/api/teams/{id}` | Delete team (if unused) | — | 204 or 409 if in use |

No pagination for teams — expected to be a small list (<50).

#### Positions (`app/backend/app/routers/positions.py`)

| Method | Path | Description | Query Params | Request Body | Response |
|--------|------|-------------|-------------|-------------|----------|
| `GET` | `/api/positions` | List positions | `status`, `team_id`, `offset`, `limit` | — | Paginated `PositionListItem[]` |
| `POST` | `/api/positions` | Create position | — | `{ title, requirements?, team_id, hiring_manager_id }` | `PositionResponse` (201) |
| `GET` | `/api/positions/{id}` | Get position detail (+ candidates) | — | — | `PositionDetailResponse` |
| `PATCH` | `/api/positions/{id}` | Update position fields | — | Partial `{ title?, requirements?, team_id?, hiring_manager_id?, status? }` | `PositionResponse` |
| `POST` | `/api/positions/{id}/archive` | Archive position | — | — | 204 |

- `PositionListItem` includes: id, title, team name, hiring manager name, status, candidate_count
- `PositionDetailResponse` extends with: requirements, list of candidates with their stages

#### Candidates (`app/backend/app/routers/candidates.py`)

| Method | Path | Description | Query Params | Request Body | Response |
|--------|------|-------------|-------------|-------------|----------|
| `GET` | `/api/candidates` | List candidates | `search`, `stage`, `position_id`, `offset`, `limit` | — | Paginated `CandidateListItem[]` |
| `POST` | `/api/candidates` | Create candidate | — | `{ full_name, email }` | `CandidateResponse` (201) |
| `GET` | `/api/candidates/{id}` | Get candidate detail (+ positions) | — | — | `CandidateDetailResponse` |
| `PATCH` | `/api/candidates/{id}` | Update candidate fields | — | Partial `{ full_name?, email? }` | `CandidateResponse` |
| `POST` | `/api/candidates/{id}/archive` | Archive candidate | — | — | 204 |
| `POST` | `/api/candidates/{id}/positions` | Link to position | — | `{ position_id }` | `CandidatePositionResponse` (201) |
| `DELETE` | `/api/candidates/{id}/positions/{position_id}` | Remove position link | — | — | 204 |
| `PATCH` | `/api/candidates/{id}/positions/{position_id}` | Update pipeline stage | — | `{ stage }` | `CandidatePositionResponse` |

- `CandidateListItem` includes: id, full_name, email, positions (array of `{ position_id, position_title, stage }`), updated_at
- `search` query param: case-insensitive partial match on full_name OR email (ILIKE)
- `stage` + `position_id` filters apply to the candidate_positions join

**Stage transition validation** (server-side, returns 422 on violation):
- Forward-only: new→screening→technical→offer→hired
- Rejected allowed from any non-terminal stage (new, screening, technical, offer)
- Cannot transition from hired or rejected
- Cannot skip stages (e.g., new→technical is invalid)

**Schemas:** `app/backend/app/schemas/teams.py`, `app/backend/app/schemas/positions.py`, `app/backend/app/schemas/candidates.py`

#### Users (existing, minor addition)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/users` | List all users (for hiring manager dropdown) |

Returns `UserResponse[]` — reuses existing schema. Added to existing auth router or a new users router.

### 2.3 Service Layer

Module-level async functions following existing pattern (session passed as param):

| File | Key Functions |
|------|--------------|
| `app/backend/app/services/team_service.py` | `list_teams`, `create_team`, `delete_team` (checks position usage) |
| `app/backend/app/services/position_service.py` | `list_positions` (with filters + pagination), `get_position`, `create_position`, `update_position`, `archive_position` |
| `app/backend/app/services/candidate_service.py` | `list_candidates` (with search/filters + pagination), `get_candidate`, `create_candidate`, `update_candidate`, `archive_candidate`, `add_to_position`, `remove_from_position`, `update_stage` (with transition validation) |

### 2.4 Frontend: Routes & Navigation

**New routes** (file-based, under `src/routes/_authenticated/`):

| File | Path | Page |
|------|------|------|
| `candidates/index.tsx` | `/candidates` | Candidate List |
| `candidates/$candidateId.tsx` | `/candidates/:candidateId` | Candidate Detail |
| `positions/index.tsx` | `/positions` | Position List |
| `positions/$positionId.tsx` | `/positions/:positionId` | Position Detail |
| `settings.tsx` | `/settings` | Settings (Teams management) |

**Navigation sidebar** (`src/widgets/sidebar.tsx`):
- Integrated into `__root.tsx` layout for authenticated users
- Links: Dashboard, Candidates, Positions, Settings
- Active link highlighted based on current route
- Collapsible (icon-only mode)

### 2.5 Frontend: Feature Modules

Following the existing Feature-Sliced Design pattern:

| Directory | Contents |
|-----------|----------|
| `src/features/candidates/` | Hooks: `useCandidates`, `useCandidate`, `useCreateCandidate`, `useUpdateCandidate`, `useArchiveCandidate`, `useAddToPosition`, `useRemoveFromPosition`, `useUpdateStage`. Schemas: Zod validation schemas for forms. |
| `src/features/positions/` | Hooks: `usePositions`, `usePosition`, `useCreatePosition`, `useUpdatePosition`, `useArchivePosition`. Schemas: Zod validation. |
| `src/features/settings/` | Hooks: `useTeams`, `useCreateTeam`, `useDeleteTeam`. |

Each hook wraps the generated TanStack Query options (from Hey API) with custom `onSuccess` logic (invalidation, navigation).

### 2.6 Frontend: New Dependencies & Components

**Install:**
```bash
bun add react-hook-form @hookform/resolvers zod
bunx shadcn@latest add table input textarea form select dialog separator skeleton tabs
```

**Key widget components** (in `src/widgets/`):
- `sidebar.tsx` — app navigation
- `candidates/candidate-table.tsx` — data table with search/filter bar
- `candidates/candidate-form.tsx` — create/edit form
- `candidates/position-link.tsx` — add-to-position dialog + stage selector
- `positions/position-table.tsx` — data table with filters
- `positions/position-form.tsx` — create/edit form
- `settings/team-manager.tsx` — team list with add/remove

### 2.7 API Client Regeneration

After backend endpoints are built:
1. Start backend dev server → export OpenAPI JSON
2. Copy `openapi.json` to `app/frontend/`
3. Run `bun run generate:api` to regenerate typed client + TanStack Query hooks
4. Build feature hooks wrapping generated options

---

## 3. Impact and Risk Analysis

**System Dependencies:**
- New models depend on existing `users` table (FK for hiring_manager_id)
- Frontend navigation change (sidebar) affects the root layout — all pages impacted visually
- API client regeneration required after backend endpoints are ready — frontend blocked until then (can use mock data initially)

**Risks & Mitigations:**

| Risk | Mitigation |
|------|-----------|
| Many-to-many queries (candidate list with positions/stages) could generate N+1 queries | Use `selectinload` / joined load for relationships in list queries; test with realistic data volume |
| Stage transition logic could have edge cases | Strict server-side validation with explicit transition map; comprehensive unit tests for every valid and invalid transition |
| Email uniqueness race condition on concurrent creates | Database unique constraint handles this — catch IntegrityError and return 409 |
| Frontend/backend schema drift after API changes | Regenerate API client as part of workflow; CI catches type mismatches |

---

## 4. Testing Strategy

### 4.1 Backend Tests

- **Unit tests** for stage transition validation logic (every valid path + every invalid path)
- **Integration tests** per router: CRUD happy paths, validation errors (duplicate email, invalid stage transition, delete team in use), filter/search combinations, pagination edge cases, archive behavior
- Follow existing pattern: pytest-asyncio, aiosqlite in-memory, `AsyncClient` with dependency overrides
- Files: `tests/test_candidates.py`, `tests/test_positions.py`, `tests/test_teams.py`

### 4.2 Browser Test Plan (Local E2E via Playwright)

**Prerequisites:** Both servers running locally — frontend at `http://localhost:5173`, backend at `http://localhost:8000`. User is logged in (dev login or Google OAuth).

Each scenario is designed to be executed sequentially using the Playwright browser tool. Scenarios build on each other — data created in earlier scenarios is used by later ones.

---

#### Scenario 0: Login & Verify Navigation

**Goal:** Confirm auth works and sidebar navigation is present.

| # | Action | Expected Result |
|---|--------|-----------------|
| 0.1 | Navigate to `http://localhost:5173` | Redirected to login page (or dashboard if already logged in) |
| 0.2 | Log in (dev login or Google OAuth) | Redirected to dashboard |
| 0.3 | Verify sidebar is visible | Sidebar contains links: Dashboard, Candidates, Positions, Settings |
| 0.4 | Verify "Dashboard" link is active/highlighted | Active state styling visible |

---

#### Scenario 1: Team Management (Settings)

**Goal:** Create teams needed for positions. Verify add/remove + validation.

| # | Action | Expected Result |
|---|--------|-----------------|
| 1.1 | Click "Settings" in sidebar | Settings page loads, Teams section visible |
| 1.2 | Verify team list is empty | Empty state or no teams listed |
| 1.3 | Type "Engineering" in team name input, click Add | "Engineering" appears in team list |
| 1.4 | Add team "Design" | "Design" appears in team list (2 teams total) |
| 1.5 | Add team "Product" | "Product" appears in team list (3 teams total) |
| 1.6 | Try adding "Engineering" again (duplicate) | Error message: duplicate rejected |
| 1.7 | Remove "Product" team (no positions use it) | Confirmation dialog appears |
| 1.8 | Confirm removal | "Product" removed, 2 teams remain |

---

#### Scenario 2: Create Positions

**Goal:** Create positions using the teams from Scenario 1.

| # | Action | Expected Result |
|---|--------|-----------------|
| 2.1 | Click "Positions" in sidebar | Position List page loads, empty state shown |
| 2.2 | Click "New Position" button | Position creation form appears |
| 2.3 | Submit form with empty fields | Validation errors: title, team, hiring manager required |
| 2.4 | Fill: title="Senior Backend Engineer", team="Engineering", hiring manager=(current user), requirements="Python, FastAPI, 5+ years" | Form populated |
| 2.5 | Submit form | Redirected to Position Detail page, all fields shown, status="Open" |
| 2.6 | Navigate back to Position List | "Senior Backend Engineer" visible in list with status "Open", 0 candidates |
| 2.7 | Create second position: title="Product Designer", team="Design", hiring manager=(current user) | Position created successfully |
| 2.8 | Verify Position List shows 2 positions | Both positions visible with correct teams and statuses |

---

#### Scenario 3: Position List Filters

**Goal:** Verify status and team filters work.

| # | Action | Expected Result |
|---|--------|-----------------|
| 3.1 | On Position List, filter by team="Engineering" | Only "Senior Backend Engineer" shown |
| 3.2 | Clear team filter, filter by team="Design" | Only "Product Designer" shown |
| 3.3 | Clear filters | Both positions shown |
| 3.4 | Open "Senior Backend Engineer" detail, change status to "On Hold", save | Status updated |
| 3.5 | Return to Position List, filter by status="Open" | Only "Product Designer" shown |
| 3.6 | Filter by status="On Hold" | Only "Senior Backend Engineer" shown |
| 3.7 | Clear filters | Both positions shown |

---

#### Scenario 4: Create Candidates

**Goal:** Create candidates and verify validation.

| # | Action | Expected Result |
|---|--------|-----------------|
| 4.1 | Click "Candidates" in sidebar | Candidate List page loads, empty state shown |
| 4.2 | Click "New Candidate" button | Candidate creation form appears |
| 4.3 | Submit with empty fields | Validation errors: name and email required |
| 4.4 | Enter name="Alice Johnson", email="not-an-email", submit | Validation error: invalid email format |
| 4.5 | Fix email to "alice@example.com", submit | Redirected to Candidate Detail page, name + email displayed, no positions linked |
| 4.6 | Navigate back, create: name="Bob Smith", email="bob@example.com" | Created successfully |
| 4.7 | Create: name="Carol Davis", email="carol@example.com" | Created successfully |
| 4.8 | Try creating: name="Duplicate Alice", email="alice@example.com" | Error: "A candidate with this email already exists." |
| 4.9 | Navigate to Candidate List | 3 candidates visible |

---

#### Scenario 5: Associate Candidates with Positions

**Goal:** Link candidates to positions and verify stage defaults to "New".

| # | Action | Expected Result |
|---|--------|-----------------|
| 5.1 | Click "Alice Johnson" in candidate list | Candidate Detail page loads |
| 5.2 | Click "Add to Position" | Position selection UI appears (shows non-archived positions only) |
| 5.3 | Select "Senior Backend Engineer" | Link created, "Senior Backend Engineer" appears with stage "New" |
| 5.4 | Click "Add to Position" again, select "Product Designer" | Second link created, both positions shown with stage "New" |
| 5.5 | Try adding "Senior Backend Engineer" again | Error: "Candidate is already associated with this position." |
| 5.6 | Navigate to "Bob Smith" detail | No positions linked |
| 5.7 | Add "Bob Smith" to "Senior Backend Engineer" | Link created, stage "New" |

---

#### Scenario 6: Pipeline Stage Transitions

**Goal:** Advance stages, verify forward-only + reject rules.

| # | Action | Expected Result |
|---|--------|-----------------|
| 6.1 | On Alice's detail, for "Senior Backend Engineer": change stage to "Screening" | Stage updates to "Screening" |
| 6.2 | Advance to "Technical" | Stage updates to "Technical" |
| 6.3 | Verify backward move is not available (no option to go back to "Screening") | UI does not offer backward transitions |
| 6.4 | Advance to "Offer" | Stage updates to "Offer" |
| 6.5 | Advance to "Hired" | Stage updates to "Hired" (terminal) |
| 6.6 | Verify no further stage changes available for this position link | No transition options shown for "Hired" |
| 6.7 | For Alice's "Product Designer" link: set stage to "Rejected" from "New" | Stage updates to "Rejected" (terminal) |
| 6.8 | Verify no further changes available | No transition options for "Rejected" |
| 6.9 | On Bob's detail, for "Senior Backend Engineer": advance New→Screening→Technical, then Reject | Rejected from "Technical" — stage shows "Rejected" |

---

#### Scenario 7: Candidate List — Search & Filters

**Goal:** Verify search, stage filter, position filter, combined filters, sorting.

| # | Action | Expected Result |
|---|--------|-----------------|
| 7.1 | Navigate to Candidate List | All 3 candidates visible |
| 7.2 | Type "alice" in search bar | Only "Alice Johnson" shown |
| 7.3 | Clear search, type "example.com" | All 3 shown (all share domain) |
| 7.4 | Clear search, type "bob" | Only "Bob Smith" shown |
| 7.5 | Clear search | All 3 visible |
| 7.6 | Filter by stage="Hired" | Only Alice shown (hired for Backend Engineer) |
| 7.7 | Filter by stage="Rejected" | Alice (Product Designer) and Bob (Backend Engineer) shown |
| 7.8 | Clear stage filter, filter by position="Senior Backend Engineer" | Alice and Bob shown |
| 7.9 | Combine: position="Senior Backend Engineer" + stage="Hired" | Only Alice shown |
| 7.10 | Click "Clear filters" | All 3 candidates shown |
| 7.11 | Click "Name" column header | Sorted alphabetically (Alice, Bob, Carol) |
| 7.12 | Click "Name" again | Reverse alphabetical (Carol, Bob, Alice) |

---

#### Scenario 8: Edit Candidate & Position

**Goal:** Verify edit + save flows and email uniqueness on edit.

| # | Action | Expected Result |
|---|--------|-----------------|
| 8.1 | Open Carol's detail page | Name and email displayed |
| 8.2 | Edit name to "Carol Williams", click Save | Name updates, page reflects new name |
| 8.3 | Edit email to "bob@example.com" (taken), click Save | Error: "A candidate with this email already exists." |
| 8.4 | Fix email to "carol.w@example.com", click Save | Email updated successfully |
| 8.5 | Navigate to "Product Designer" position detail | Position fields shown |
| 8.6 | Edit title to "Senior Product Designer", click Save | Title updated |
| 8.7 | Verify Position List reflects new title | "Senior Product Designer" shown |

---

#### Scenario 9: Archive

**Goal:** Verify soft delete hides records from lists and dropdowns.

| # | Action | Expected Result |
|---|--------|-----------------|
| 9.1 | Open Carol's detail page, click "Archive" | Confirmation dialog: "Archive Carol Williams?" |
| 9.2 | Confirm archive | Redirected to Candidate List — Carol is NOT visible |
| 9.3 | Verify Candidate List shows 2 candidates (Alice, Bob) | Carol hidden |
| 9.4 | Navigate to "Senior Product Designer" position detail, click "Archive" | Confirmation dialog appears |
| 9.5 | Confirm archive | Redirected to Position List — position not visible |
| 9.6 | Verify Position List shows 1 position | Only "Senior Backend Engineer" remains |
| 9.7 | Open Alice's detail, click "Add to Position" | Archived "Senior Product Designer" does NOT appear in dropdown |

---

#### Scenario 10: Team Deletion Constraint

**Goal:** Verify teams used by positions (including archived) cannot be removed.

| # | Action | Expected Result |
|---|--------|-----------------|
| 10.1 | Navigate to Settings | Teams page: "Engineering" and "Design" listed |
| 10.2 | Try removing "Engineering" | Blocked: "This team is assigned to N position(s) and cannot be removed." |
| 10.3 | Try removing "Design" (archived position still references it) | Blocked: same message |

---

#### Scenario 11: Position Detail — Candidate List

**Goal:** Verify position detail shows associated candidates with stages.

| # | Action | Expected Result |
|---|--------|-----------------|
| 11.1 | Open "Senior Backend Engineer" position detail | Candidates section shows Alice (Hired) and Bob (Rejected) |
| 11.2 | Verify candidate count in Position List matches | Shows "2" in candidate count column |

---

#### Scenario 12: Empty States & Edge Cases

**Goal:** Verify UI handles empty data gracefully.

| # | Action | Expected Result |
|---|--------|-----------------|
| 12.1 | Filter Candidate List by stage="Offer" | Empty state: no candidates match, message shown |
| 12.2 | Search for "nonexistent" | Empty state: no results |
| 12.3 | Navigate to a candidate detail with no positions (create a new candidate) | "No positions linked" message, "Add to Position" button available |
