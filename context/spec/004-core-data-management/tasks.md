# Task List: Core Data Management (004)

- **Spec:** `context/spec/004-core-data-management/`
- **Status:** Completed
- **Slices:** 11 (0–10)

---

## Prerequisites

- Backend dev server: `uv run fastapi dev` in `app/backend/`
- Frontend dev server: `bun run dev` in `app/frontend/`
- PostgreSQL running locally (or dev DB)
- Playwright browser MCP available for E2E verification

---

- [x] **Slice 0: Foundation — Models, Migration, Sidebar, Skeleton Routes**
  - [x] Create `app/backend/app/models/enums.py` — `PositionStatus` and `PipelineStage` StrEnums **[Agent: python-architect]**
  - [x] Create models: `team.py`, `candidate.py`, `position.py`, `candidate_position.py` in `app/backend/app/models/` with FKs, unique constraints, `is_archived`, timestamps **[Agent: python-architect]**
  - [x] Update `app/backend/app/models/__init__.py` to import all new models **[Agent: python-architect]**
  - [x] Generate Alembic migration: `uv run alembic revision --autogenerate -m "add_core_data_tables"` and apply with `uv run alembic upgrade head` **[Agent: Bash]**
  - [x] Install frontend deps: `bun add react-hook-form @hookform/resolvers zod` and shadcn components: `bunx shadcn@latest add table input textarea form select dialog separator skeleton tabs` **[Agent: Bash]**
  - [x] Create sidebar widget `src/widgets/sidebar/` with nav links (Dashboard, Candidates, Positions, Settings), active link highlighting, collapsible mode **[Agent: react-architect]**
  - [x] Create skeleton route files under `src/routes/_authenticated/`: `candidates/index.tsx`, `candidates/$candidateId.tsx`, `positions/index.tsx`, `positions/$positionId.tsx`, `settings.tsx` — each with minimal placeholder content **[Agent: react-architect]**
  - [x] Integrate sidebar into authenticated layout **[Agent: react-architect]**
  - [x] Verify: backend starts, migration applied, frontend starts, sidebar renders with working links to skeleton pages **[Agent: general-purpose]** *(Requires: Playwright browser MCP, both dev servers)*

---

- [x] **Slice 1: Team Management (Settings Page)**
  - [x] Create `app/backend/app/services/team_service.py` — `list_teams`, `create_team`, `delete_team` (checks position usage including archived) **[Agent: python-architect]**
  - [x] Create `app/backend/app/schemas/teams.py` — `TeamCreate`, `TeamResponse` **[Agent: python-architect]**
  - [x] Create `app/backend/app/routers/teams.py` — GET `/api/teams`, POST `/api/teams`, DELETE `/api/teams/{id}` **[Agent: python-architect]**
  - [x] Register teams router in `main.py` **[Agent: python-architect]**
  - [x] Create `app/backend/tests/test_teams.py` — CRUD happy paths, duplicate name rejection, delete team in use blocked **[Agent: python-architect]**
  - [x] Run backend tests: `uv run pytest tests/test_teams.py` **[Agent: Bash]**
  - [x] Regenerate API client: start backend → export OpenAPI JSON → `bun run generate:api` **[Agent: Bash]**
  - [x] Create `src/features/settings/` — hooks: `useTeams`, `useCreateTeam`, `useDeleteTeam` **[Agent: react-architect]**
  - [x] Implement Settings route — team list, add input, remove button with confirmation dialog **[Agent: react-architect]**
  - [x] Browser verify (Scenario 1): Navigate to Settings, add "Engineering"/"Design"/"Product", try duplicate, remove "Product" **[Agent: general-purpose]** *(Requires: Playwright browser MCP)*

---

- [x] **Slice 2: Positions — Create & List**
  - [x] Create `app/backend/app/services/position_service.py` — `list_positions` (basic), `create_position` **[Agent: python-architect]**
  - [x] Create `app/backend/app/schemas/positions.py` — `PositionCreate`, `PositionResponse`, `PositionListItem`, pagination envelope **[Agent: python-architect]**
  - [x] Create `app/backend/app/routers/positions.py` — GET `/api/positions`, POST `/api/positions` **[Agent: python-architect]**
  - [x] Add GET `/api/users` endpoint — list all users for hiring manager dropdown **[Agent: python-architect]**
  - [x] Register routers in `main.py` **[Agent: python-architect]**
  - [x] Create `app/backend/tests/test_positions.py` — create position, list positions, required field validation **[Agent: python-architect]**
  - [x] Run tests: `uv run pytest tests/test_positions.py` **[Agent: Bash]**
  - [x] Regenerate API client **[Agent: Bash]**
  - [x] Create `src/features/positions/` — hooks: `usePositions`, `useCreatePosition`, `useUsers` **[Agent: react-architect]**
  - [x] Implement Position List route — table (title, team, HM, status, candidate count), "New Position" button **[Agent: react-architect]**
  - [x] Implement Position create form — title, requirements textarea, team dropdown, HM dropdown, validation (zod) **[Agent: react-architect]**
  - [x] Browser verify (Scenario 2): Navigate to Positions, see empty state, create "Senior Backend Engineer" + "Product Designer", verify list **[Agent: general-purpose]** *(Requires: Playwright browser MCP)*

---

- [x] **Slice 3: Position Detail, Edit & List Filters**
  - [x] Add `get_position`, `update_position` to position_service.py **[Agent: python-architect]**
  - [x] Add `status` + `team_id` filter params to `list_positions` **[Agent: python-architect]**
  - [x] Add routes: GET `/api/positions/{id}`, PATCH `/api/positions/{id}` **[Agent: python-architect]**
  - [x] Create `PositionDetailResponse` schema (extends with requirements, candidates+stages list) **[Agent: python-architect]**
  - [x] Add tests: get detail, update fields, filter by status, filter by team **[Agent: python-architect]**
  - [x] Run tests: `uv run pytest tests/test_positions.py` **[Agent: Bash]**
  - [x] Regenerate API client **[Agent: Bash]**
  - [x] Add hooks: `usePosition`, `useUpdatePosition` **[Agent: react-architect]**
  - [x] Implement Position Detail route — all fields, edit form, save button, candidates section **[Agent: react-architect]**
  - [x] Add status + team filter dropdowns to Position List **[Agent: react-architect]**
  - [x] Browser verify (Scenario 3): Edit position status to "On Hold", filter list by status and team **[Agent: general-purpose]** *(Requires: Playwright browser MCP)*

---

- [x] **Slice 4: Candidates — Create & List (Basic)**
  - [x] Create `app/backend/app/services/candidate_service.py` — `list_candidates` (basic), `create_candidate` **[Agent: python-architect]**
  - [x] Create `app/backend/app/schemas/candidates.py` — `CandidateCreate`, `CandidateResponse`, `CandidateListItem`, pagination envelope **[Agent: python-architect]**
  - [x] Create `app/backend/app/routers/candidates.py` — GET `/api/candidates`, POST `/api/candidates` **[Agent: python-architect]**
  - [x] Register candidates router in `main.py` **[Agent: python-architect]**
  - [x] Create `app/backend/tests/test_candidates.py` — create candidate, duplicate email rejection, list candidates **[Agent: python-architect]**
  - [x] Run tests: `uv run pytest tests/test_candidates.py` **[Agent: Bash]**
  - [x] Regenerate API client **[Agent: Bash]**
  - [x] Create `src/features/candidates/` — hooks: `useCandidates`, `useCreateCandidate` **[Agent: react-architect]**
  - [x] Implement Candidate List route — table (name, email, positions, stage, updated), "New Candidate" button **[Agent: react-architect]**
  - [x] Implement Candidate create form — name + email, zod validation **[Agent: react-architect]**
  - [x] Browser verify (Scenario 4): Create Alice/Bob/Carol, try duplicate email, verify list shows 3 **[Agent: general-purpose]** *(Requires: Playwright browser MCP)*

---

- [x] **Slice 5: Candidate Detail & Edit**
  - [x] Add `get_candidate`, `update_candidate` to candidate_service.py **[Agent: python-architect]**
  - [x] Add routes: GET `/api/candidates/{id}`, PATCH `/api/candidates/{id}` **[Agent: python-architect]**
  - [x] Create `CandidateDetailResponse` schema (includes position-stage list, dates) **[Agent: python-architect]**
  - [x] Add tests: get detail, update name/email, email uniqueness on edit **[Agent: python-architect]**
  - [x] Run tests: `uv run pytest tests/test_candidates.py` **[Agent: Bash]**
  - [x] Regenerate API client **[Agent: Bash]**
  - [x] Add hooks: `useCandidate`, `useUpdateCandidate` **[Agent: react-architect]**
  - [x] Implement Candidate Detail route — name, email, created/updated dates, positions section (empty for now), edit form, save button **[Agent: react-architect]**
  - [x] Browser verify (Scenario 8 partial): Edit candidate name, try duplicate email → error, save successfully **[Agent: general-purpose]** *(Requires: Playwright browser MCP)*

---

- [x] **Slice 6: Candidate-Position Association**
  - [x] Add `add_to_position`, `remove_from_position` to candidate_service.py **[Agent: python-architect]**
  - [x] Add routes: POST `/api/candidates/{id}/positions`, DELETE `/api/candidates/{id}/positions/{position_id}` **[Agent: python-architect]**
  - [x] Create `CandidatePositionResponse` schema **[Agent: python-architect]**
  - [x] Add tests: link candidate to position, duplicate link rejection, remove link **[Agent: python-architect]**
  - [x] Run tests: `uv run pytest tests/test_candidates.py` **[Agent: Bash]**
  - [x] Regenerate API client **[Agent: Bash]**
  - [x] Add hooks: `useAddToPosition`, `useRemoveFromPosition` **[Agent: react-architect]**
  - [x] Add "Add to Position" dialog to Candidate Detail — shows non-archived positions only **[Agent: react-architect]**
  - [x] Display linked positions with stages on Candidate Detail **[Agent: react-architect]**
  - [x] Add remove-from-position action with confirmation dialog **[Agent: react-architect]**
  - [x] Update Position Detail candidates section to show linked candidates with stages **[Agent: react-architect]**
  - [x] Browser verify (Scenario 5): Add Alice to both positions, try duplicate, add Bob to Backend Engineer. Verify "New" default stage. **[Agent: general-purpose]** *(Requires: Playwright browser MCP)*

---

- [x] **Slice 7: Pipeline Stage Tracking**
  - [x] Implement stage transition validation logic (forward-only map, reject-from-any, no-change-from-terminal) in candidate_service.py **[Agent: python-architect]**
  - [x] Add `update_stage` function to candidate_service.py **[Agent: python-architect]**
  - [x] Add route: PATCH `/api/candidates/{id}/positions/{position_id}` with `{ stage }` body **[Agent: python-architect]**
  - [x] Add comprehensive stage transition tests — every valid path (N→S, S→T, T→O, O→H, N/S/T/O→R) and every invalid path (backward, skip, from terminal) **[Agent: python-architect]**
  - [x] Run tests: `uv run pytest tests/test_candidates.py -k stage` **[Agent: Bash]**
  - [x] Regenerate API client **[Agent: Bash]**
  - [x] Add hook: `useUpdateStage` **[Agent: react-architect]**
  - [x] Add stage selector to each candidate-position row on Candidate Detail — shows only valid next stages, single-click action **[Agent: react-architect]**
  - [x] Browser verify (Scenario 6): Advance Alice through full pipeline to Hired. Reject Alice from another position. Reject Bob from Technical. Verify no backward/terminal options. **[Agent: general-purpose]** *(Requires: Playwright browser MCP)*

---

- [x] **Slice 8: Candidate List — Search, Filters & Sort**
  - [x] Add `search` (ILIKE on name/email), `stage`, `position_id` query params and sort support to `list_candidates` **[Agent: python-architect]**
  - [x] Update GET `/api/candidates` to accept filter/search/sort params **[Agent: python-architect]**
  - [x] Add tests: search by name, by email, stage filter, position filter, combined filters, sort, empty results **[Agent: python-architect]**
  - [x] Run tests: `uv run pytest tests/test_candidates.py -k "search or filter or sort"` **[Agent: Bash]**
  - [x] Regenerate API client **[Agent: Bash]**
  - [x] Add search input, stage filter dropdown, position filter dropdown, "Clear filters" button to Candidate List **[Agent: react-architect]**
  - [x] Add sortable column headers (name, email, updated_at) with toggle asc/desc **[Agent: react-architect]**
  - [x] Browser verify (Scenario 7): Search "alice", filter by Hired, filter by position, combine filters, sort by name asc/desc **[Agent: general-purpose]** *(Requires: Playwright browser MCP)*

---

- [x] **Slice 9: Archive & Constraints**
  - [x] Add `archive_candidate` to candidate_service.py, `archive_position` to position_service.py **[Agent: python-architect]**
  - [x] Add routes: POST `/api/candidates/{id}/archive`, POST `/api/positions/{id}/archive` **[Agent: python-architect]**
  - [x] Ensure `delete_team` checks archived positions too **[Agent: python-architect]**
  - [x] Add tests: archive candidate (hidden from list), archive position (hidden from list + dropdowns), team deletion blocked by archived position **[Agent: python-architect]**
  - [x] Run tests: `uv run pytest` **[Agent: Bash]**
  - [x] Regenerate API client **[Agent: Bash]**
  - [x] Add hooks: `useArchiveCandidate`, `useArchivePosition` **[Agent: react-architect]**
  - [x] Add Archive button + confirmation dialog to Candidate Detail and Position Detail **[Agent: react-architect]**
  - [x] Ensure archived positions excluded from "Add to Position" dropdown **[Agent: react-architect]**
  - [x] Browser verify (Scenarios 9+10): Archive Carol → hidden from list. Archive Product Designer → hidden from list + dropdown. Try removing teams → blocked. **[Agent: general-purpose]** *(Requires: Playwright browser MCP)*

---

- [x] **Slice 10: Polish, Empty States & Full E2E**
  - [x] Add empty state messages: Candidate List (no candidates), Position List (no positions), filtered results (no matches), Candidate Detail positions section (no positions linked) **[Agent: react-architect]**
  - [x] Verify Position Detail candidate count matches Position List display **[Agent: react-architect]**
  - [x] Verify multi-position candidates render correctly in Candidate List (e.g. "Backend Engineer: Hired, Product Designer: Rejected") **[Agent: react-architect]**
  - [x] Run full backend test suite: `uv run pytest` — all tests pass **[Agent: Bash]**
  - [x] Full browser E2E: execute all scenarios (0–12) sequentially from the test plan in technical-considerations.md §4.2 **[Agent: general-purpose]** *(Requires: Playwright browser MCP, both dev servers running)*
