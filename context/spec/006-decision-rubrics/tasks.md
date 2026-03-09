# Tasks: Decision Rubric Management

- **Functional Spec:** `context/spec/006-decision-rubrics/functional-spec.md`
- **Technical Spec:** `context/spec/006-decision-rubrics/technical-considerations.md`

---

## Slice 1: Empty rubric templates section on Settings page

The smallest end-to-end increment: schema exists, API returns empty list, Settings page shows the section.

- [x] **Backend: Create `rubric_templates` table and model.** Create Alembic migration for `rubric_templates` table. Create `RubricTemplate` SQLModel in `models/rubric_template.py`. Register in `models/__init__.py`. **[Agent: python-architect]**
- [x] **Backend: Create list templates endpoint.** Create `schemas/rubric_templates.py` with `RubricTemplateListItem` and list response schema. Create `services/rubric_template_service.py` with `list_templates()` returning active (non-archived) templates. Create `routers/rubric_templates.py` with `GET /api/rubric-templates` (authenticated via `Depends(get_current_user)`). Register router in `main.py`. **[Agent: python-architect]**
- [x] **Frontend: Add "Rubric Templates" section to Settings page.** Regenerate API client (`uv run python scripts/export_openapi.py` then `bun run generate:api`). Create `features/rubrics/hooks/use-rubric-templates.ts` and barrel export `features/rubrics/index.ts`. Create `widgets/rubrics/rubric-template-table.tsx` (empty state + table structure). Add "Rubric Templates" section to `routes/_authenticated/settings.tsx` below "Teams" section. **[Agent: react-architect]**
- [x] **Verification:** Run backend, apply migration. `curl -H "Authorization: ..." GET /api/rubric-templates` — expect `{"items": [], "total": 0}`. Start frontend, navigate to Settings — see "Rubric Templates" section with empty state message. Run `bun run build && bun run lint` — no errors. **[Agent: general-purpose]**

---

## Slice 2: Create rubric template with rubric editor

Core complexity: the rubric editor widget and template creation flow.

- [x] **Backend: Create shared rubric structure validation.** Create `schemas/rubric_structure.py` with Pydantic models `RubricCriterion`, `RubricCategory`, `RubricStructure`. Add validators: category weights sum to 100, criterion weights per category sum to 100, at least one category, each category has at least one criterion. **[Agent: python-architect]**
- [x] **Backend: Create and get template endpoints.** Add `create_template()` and `get_template()` to `rubric_template_service.py` — validates structure via `RubricStructure`, saves to DB. Add `POST /api/rubric-templates` and `GET /api/rubric-templates/{id}` to router (both authenticated). **[Agent: python-architect]**
- [x] **Backend: Write tests for template creation.** Valid structure saves (201), invalid weight sums return 422, missing required fields return 422, unauthenticated returns 401. **[Agent: python-architect]**
- [x] **Frontend: Build rubric editor widget.** Build `widgets/rubrics/rubric-editor.tsx` — form-based editor using `react-hook-form` + `useFieldArray` + zod. Supports: add/edit/delete/reorder categories and criteria via up/down arrow buttons, real-time weight total indicators per level, save blocked with inline error when weights are invalid. **[Agent: react-architect]**
- [x] **Frontend: Build template create dialog and wire into Settings.** Regenerate API client. Build `widgets/rubrics/template-editor-dialog.tsx` wrapping rubric editor for create mode. Create `use-create-rubric-template` hook (invalidates template list on success). Wire into Settings page: "Create Template" button opens dialog, on save template appears in table. **[Agent: react-architect]**
- [x] **Verification:** Create a template via the UI with 2 categories (weights 60/40) and 2-3 criteria each (weights summing to 100%). Verify it appears in the table. Attempt to save with category weights summing to 80% — verify save is blocked with error message. Run `bun run build && bun run lint` — no errors. **[Agent: general-purpose]**

---

## Slice 3: Edit, duplicate, and archive rubric templates

Complete template lifecycle management.

- [x] **Backend: Add update, duplicate, archive endpoints.** Add `update_template()`, `duplicate_template()`, `archive_template()` to service. `archive_template` returns `position_count` (count of position rubrics cloned from this template — initially 0). Add `PATCH /api/rubric-templates/{id}`, `POST /api/rubric-templates/{id}/duplicate`, `POST /api/rubric-templates/{id}/archive` to router (all authenticated). **[Agent: python-architect]**
- [x] **Backend: Write tests for update, duplicate, archive.** Update changes fields. Duplicate creates copy with "(Copy)" suffix. Archive sets `is_archived=true` and filters from list. Archived template returns 404 on get. **[Agent: python-architect]**
- [x] **Frontend: Add edit, duplicate, archive actions.** Regenerate API client. Update `template-editor-dialog.tsx` to support edit mode (pre-filled with existing structure). Create `use-update-rubric-template`, `use-duplicate-rubric-template`, `use-archive-rubric-template` hooks. Add action buttons (Edit, Duplicate, Archive) to `rubric-template-table.tsx`. Archive shows confirmation dialog with position count warning. **[Agent: react-architect]**
- [x] **Verification:** Edit a template's name and structure — verify changes persist on reload. Duplicate — verify copy appears with "(Copy)" suffix. Archive — verify template disappears from list. Run `bun run build && bun run lint` — no errors. **[Agent: general-purpose]**

---

## Slice 4: Seed default rubric templates

4 default templates available on fresh setup.

- [x] **Backend: Create data migration for default templates.** Create Alembic data migration `seed_default_rubric_templates` that inserts 4 templates (Software Engineer, Product Manager, Designer, Data Scientist) with realistic category/criteria structures (3–4 categories, 2–4 criteria each). Only inserts if table is empty. **[Agent: python-architect]**
- [x] **Verification:** Reset DB (`alembic downgrade base && alembic upgrade head`). Open Settings → verify 4 templates present with correct names and category counts. Click into one to verify structure looks reasonable. **[Agent: general-purpose]**

---

## Slice 5: Assign rubric to position (from template or custom)

Position detail page shows rubric status; users can assign a rubric.

- [x] **Backend: Create position rubric tables and models.** Create Alembic migration for `position_rubrics` and `position_rubric_versions` tables (with `ON DELETE CASCADE` from position_rubrics to versions, and from positions to position_rubrics). Create `PositionRubric` + `PositionRubricVersion` SQLModels in `models/position_rubric.py`. Register in `models/__init__.py`. **[Agent: python-architect]**
- [x] **Backend: Create position rubric endpoints.** Create `schemas/position_rubrics.py` with create/response schemas. Create `services/position_rubric_service.py` with `create_rubric()` (handles `template` source — clones structure, and `custom` source — accepts structure; creates version 1 with `created_by_id` from current user) and `get_active_rubric()` (returns latest version). Create `routers/position_rubrics.py` with `POST /api/positions/{id}/rubric` and `GET /api/positions/{id}/rubric` (both authenticated, pass `current_user.id` to service). Register router in `main.py`. **[Agent: python-architect]**
- [x] **Backend: Write tests for position rubric creation.** Create from template clones structure correctly. Create custom with valid structure. 409 if position already has rubric. 404 if position not found. Unauthenticated returns 401. **[Agent: python-architect]**
- [x] **Frontend: Build rubric summary card and assign dialog.** Regenerate API client. Create `use-position-rubric`, `use-create-position-rubric` hooks. Build `widgets/rubrics/rubric-summary-card.tsx` — shows source (template name or "Custom"), category count, version number when rubric exists; shows "Add Rubric" prompt when none. Build `widgets/rubrics/assign-rubric-dialog.tsx` — two options: "Use Template" (dropdown of active templates) or "Create Custom" (opens rubric editor). **[Agent: react-architect]**
- [x] **Frontend: Add rubric card to position detail page.** Add `RubricSummaryCard` to `routes/_authenticated/positions/$positionId.tsx` between `PositionInfoCard` and `PositionCandidatesTable`. **[Agent: react-architect]**
- [x] **Verification:** Navigate to a position with no rubric — see "Add Rubric" prompt. Assign from template — see summary card with template name and "v1". Create another position, assign custom rubric — see summary card with "Custom" source. Run `bun run build && bun run lint` — no errors. **[Agent: general-purpose]**

---

## Slice 6: Edit position rubric (creates new version)

Editing a rubric increments the version.

- [x] **Backend: Add update rubric endpoint.** Add `update_rubric()` to service — validates structure, creates new version with `version_number = max + 1`, uses `SELECT ... FOR UPDATE` for race safety, records `created_by_id` from current user. Add `PUT /api/positions/{id}/rubric` to router (authenticated). **[Agent: python-architect]**
- [x] **Backend: Write tests for rubric update.** Update creates new version. Version number increments. Structure is validated (422 on invalid weights). 404 if no rubric exists. **[Agent: python-architect]**
- [x] **Frontend: Add edit action to rubric summary card.** Regenerate API client. Create `use-update-position-rubric` hook. Add "Edit" action to `rubric-summary-card.tsx` — opens rubric editor dialog pre-filled with current structure. On save, summary card refreshes and shows incremented version number. **[Agent: react-architect]**
- [x] **Verification:** Edit a position rubric, save. Verify summary card shows "v2". Edit again, verify "v3". Run `bun run build && bun run lint` — no errors. **[Agent: general-purpose]**

---

## Slice 7: Delete position rubric

Remove rubric and all versions.

- [x] **Backend: Add delete rubric endpoint.** Add `delete_rubric()` to service — deletes `position_rubric` row (cascades to versions). Add `DELETE /api/positions/{id}/rubric` to router (authenticated). **[Agent: python-architect]**
- [x] **Backend: Write test for rubric deletion.** Delete removes rubric. `GET` returns 404 after deletion. Can re-assign after delete. **[Agent: python-architect]**
- [x] **Frontend: Add delete action to rubric summary card.** Regenerate API client. Create `use-delete-position-rubric` hook. Add "Delete" action to `rubric-summary-card.tsx` — confirmation dialog: "Remove rubric from [Position Name]? All versions will be deleted." On confirm, card reverts to "Add Rubric" prompt. **[Agent: react-architect]**
- [x] **Verification:** Delete a position's rubric. Verify summary card shows "Add Rubric" prompt. Assign a new rubric — verify it works. Run `bun run build && bun run lint` — no errors. **[Agent: general-purpose]**

---

## Slice 8: Version history, view, and revert

Browse past versions, view read-only, revert to any version.

- [x] **Backend: Add version history and revert endpoints.** Add `list_versions()`, `get_version()`, `revert_to_version()` to service. Revert creates a new version copying the target version's structure, records `created_by_id`. Add `GET /api/positions/{id}/rubric/versions`, `GET /api/positions/{id}/rubric/versions/{version_number}`, `POST /api/positions/{id}/rubric/revert/{version_number}` to router (all authenticated). **[Agent: python-architect]**
- [x] **Backend: Write tests for version history and revert.** List returns all versions sorted desc. Get specific version returns correct structure. Revert creates new version with correct structure and incremented number. Intermediate versions are preserved. **[Agent: python-architect]**
- [x] **Frontend: Build version history dialog.** Regenerate API client. Create `use-rubric-versions`, `use-revert-rubric-version` hooks. Build `widgets/rubrics/version-history-dialog.tsx` — lists versions (number, creator name, date). Click version to view read-only rubric structure. "Revert to this version" button with confirmation. Add "View History" action to `rubric-summary-card.tsx`. **[Agent: react-architect]**
- [x] **Verification:** Create rubric (v1), edit (v2), edit again (v3). Open history — see 3 versions. View v1 read-only — correct structure. Revert to v1 — verify v4 is created with v1's structure. Summary card shows "v4". History now shows 4 entries. Run `bun run build && bun run lint` — no errors. **[Agent: general-purpose]**

---

## Slice 9: Save position rubric as template

Create a reusable template from a position's active rubric.

- [x] **Backend: Add save-as-template endpoint.** Add `save_as_template()` to `position_rubric_service.py` — reads active version structure, creates new `RubricTemplate` with user-provided name/description. Add `POST /api/positions/{id}/rubric/save-as-template` to router (authenticated). **[Agent: python-architect]**
- [x] **Backend: Write test for save-as-template.** Saves template with correct name and structure. Template appears in template list. 404 if no rubric exists. **[Agent: python-architect]**
- [x] **Frontend: Add save-as-template action.** Regenerate API client. Create `use-save-rubric-as-template` hook (invalidates template list). Add "Save as Template" action to `rubric-summary-card.tsx` — dialog asking for template name and optional description. On success, confirmation message. **[Agent: react-architect]**
- [x] **Verification:** Save a position rubric as template "My Custom Template". Navigate to Settings → verify "My Custom Template" appears in template list with matching category count. Run `bun run build && bun run lint` — no errors. **[Agent: general-purpose]**

---

## Slice 10: Final CI verification and code review

Ensure everything passes CI and review the complete feature against acceptance criteria.

- [x] **Backend: Full CI check.** Run `uv run pytest` (all tests pass), `uv run ruff check .`, `uv run ruff format . --check`, `uv run mypy app/`. Regenerate OpenAPI spec and verify freshness. Fix any issues. **[Agent: python-architect]**
- [x] **Frontend: Full CI check.** Run `bun run build` and `bun run lint`. Fix any issues. **[Agent: react-architect]**
- [x] **Code review.** Review all new code against functional spec acceptance criteria (§2.1–§2.6) and technical spec. Verify auth is present on all endpoints. **[Agent: superpowers:code-reviewer]**

---

## Recommendations

| Task/Slice | Issue | Recommendation |
|---|---|---|
| All verification sub-tasks | Assigned to `general-purpose` — no dedicated QA agent | Playwright browser MCP is available; `general-purpose` has access to all tools including browser and Bash. Adequate for verification. |
| Backend tests | No dedicated Python test agent | `python-architect` handles both implementation and testing. Adequate given the project uses pytest. |
