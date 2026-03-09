# Technical Specification: Decision Rubric Management

- **Functional Specification:** `context/spec/006-decision-rubrics/functional-spec.md`
- **Status:** Completed
- **Author:** Claude (AI-assisted)

---

## 1. High-Level Technical Approach

Rubric management is a self-contained CRUD feature with no external integrations. The implementation adds:

- **3 new database tables**: `rubric_templates` (with JSONB structure), `position_rubrics` (linking positions to rubrics), and `position_rubric_versions` (JSONB snapshots per version)
- **2 new backend modules**: `rubric_template_service` + `rubric_template` router for template CRUD; `position_rubric_service` + `position_rubric` router for position-scoped rubric management with versioning
- **1 new feature module** (`features/rubrics/`) with TanStack Query hooks for all rubric operations
- **New widgets** (`widgets/rubrics/`): reusable rubric editor, summary card, template table, dialogs
- **Settings page extension**: "Rubric Templates" section added below existing "Teams" section
- **Position detail extension**: Rubric summary card added between the info card and candidates table

The rubric structure (categories + criteria + weights) is stored as JSONB for both templates and position rubric versions. Weight validation runs both client-side (real-time) and server-side (on save). Templates are normalized rows; position rubric history is an append-only versions table with JSONB snapshots.

---

## 2. Proposed Solution & Implementation Plan

### Data Model / Database Changes

**Table: `rubric_templates`**

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | INTEGER | PK, autoincrement | |
| name | VARCHAR | NOT NULL | Template name |
| description | TEXT | nullable | Optional description |
| structure | JSONB | NOT NULL | Full rubric structure (see schema below) |
| is_archived | BOOLEAN | NOT NULL, default false | Soft delete |
| created_at | DATETIME | NOT NULL, server default now() | |
| updated_at | DATETIME | NOT NULL, server default now(), on update | |

**Table: `position_rubrics`**

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | INTEGER | PK, autoincrement | |
| position_id | INTEGER | FK → positions.id, UNIQUE, NOT NULL | One rubric per position |
| source_template_id | INTEGER | FK → rubric_templates.id, nullable | Tracks clone origin |
| created_at | DATETIME | NOT NULL, server default now() | |
| updated_at | DATETIME | NOT NULL, server default now(), on update | |

**Table: `position_rubric_versions`**

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | INTEGER | PK, autoincrement | |
| position_rubric_id | INTEGER | FK → position_rubrics.id, NOT NULL | ON DELETE CASCADE |
| version_number | INTEGER | NOT NULL | Sequential per rubric (1, 2, 3...) |
| structure | JSONB | NOT NULL | Full rubric snapshot |
| created_by_id | INTEGER | FK → users.id, NOT NULL | Who created this version |
| created_at | DATETIME | NOT NULL, server default now() | |

- Composite unique constraint on `(position_rubric_id, version_number)`
- Index on `position_rubric_id` for version lookups

**JSONB Structure Schema** (shared by templates and versions):

```json
{
  "categories": [
    {
      "name": "Technical Skills",
      "description": "Ability to code and design systems",
      "weight": 40,
      "sort_order": 0,
      "criteria": [
        {
          "name": "System Design",
          "description": "Can design scalable distributed systems",
          "weight": 50,
          "sort_order": 0
        },
        {
          "name": "Coding Proficiency",
          "description": null,
          "weight": 50,
          "sort_order": 1
        }
      ]
    }
  ]
}
```

- `weight` values are integers representing percentages (0–100)
- `sort_order` is a zero-based integer for display ordering
- `description` is nullable at both levels

**Migration**: Single Alembic migration `add_rubric_tables` creates all 3 tables. A second data migration `seed_default_rubric_templates` inserts the 4 default templates (Software Engineer, Product Manager, Designer, Data Scientist).

**Models to create:**
- `app/backend/app/models/rubric_template.py` — `RubricTemplate`
- `app/backend/app/models/position_rubric.py` — `PositionRubric`, `PositionRubricVersion`
- Register all in `models/__init__.py`

### API Contracts

**Authentication:** All endpoints require authentication via `current_user: User = Depends(get_current_user)`. This follows the established pattern — every route in the app injects the current user dependency. Services that create versioned records use `current_user.id` for the `created_by_id` field.

#### Rubric Templates

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/rubric-templates` | List active templates |
| POST | `/api/rubric-templates` | Create template |
| GET | `/api/rubric-templates/{id}` | Get template with structure |
| PATCH | `/api/rubric-templates/{id}` | Update template |
| POST | `/api/rubric-templates/{id}/duplicate` | Duplicate template |
| POST | `/api/rubric-templates/{id}/archive` | Archive template |

**GET `/api/rubric-templates`** — Response:
```json
{
  "items": [
    {
      "id": 1,
      "name": "Software Engineer",
      "description": "Standard rubric for SWE roles",
      "category_count": 4,
      "created_at": "2026-02-16T..."
    }
  ],
  "total": 4
}
```
No pagination needed (template count will be small), but include `total` for consistency.

**POST `/api/rubric-templates`** — Request body:
```json
{
  "name": "Software Engineer",
  "description": "Optional",
  "structure": { "categories": [...] }
}
```
Validates weight sums before saving. Returns 422 if invalid.

**PATCH `/api/rubric-templates/{id}`** — Request body (all optional):
```json
{
  "name": "Updated Name",
  "description": "Updated",
  "structure": { "categories": [...] }
}
```
If `structure` is provided, validates weights.

**POST `/api/rubric-templates/{id}/duplicate`** — No request body. Creates copy with name `"{Original} (Copy)"`. Returns the new template.

**POST `/api/rubric-templates/{id}/archive`** — Response includes `position_count` (number of position rubrics that were cloned from this template) for the frontend warning display:
```json
{
  "id": 1,
  "is_archived": true,
  "position_count": 3
}
```

#### Position Rubrics

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/positions/{id}/rubric` | Get active rubric (latest version) |
| POST | `/api/positions/{id}/rubric` | Create rubric (from template or custom) |
| PUT | `/api/positions/{id}/rubric` | Update rubric (creates new version) |
| DELETE | `/api/positions/{id}/rubric` | Delete rubric and all versions |
| GET | `/api/positions/{id}/rubric/versions` | List version history |
| GET | `/api/positions/{id}/rubric/versions/{version_number}` | Get specific version |
| POST | `/api/positions/{id}/rubric/revert/{version_number}` | Revert to version (creates new version) |
| POST | `/api/positions/{id}/rubric/save-as-template` | Save active version as new template |

**GET `/api/positions/{id}/rubric`** — Response:
```json
{
  "id": 1,
  "position_id": 5,
  "source_template_name": "Software Engineer",
  "version_number": 2,
  "structure": { "categories": [...] },
  "created_by": "Jane Smith",
  "created_at": "2026-02-16T..."
}
```
Returns 404 if no rubric assigned.

**POST `/api/positions/{id}/rubric`** — Request body:
```json
{
  "source": "template",
  "template_id": 1,
  "structure": null
}
```
or for custom:
```json
{
  "source": "custom",
  "template_id": null,
  "structure": { "categories": [...] }
}
```
When `source` is `"template"`, the structure is cloned from the template. Returns 409 if position already has a rubric.

**PUT `/api/positions/{id}/rubric`** — Request body:
```json
{
  "structure": { "categories": [...] }
}
```
Creates a new version with `version_number = current + 1`. Validates weights.

**POST `/api/positions/{id}/rubric/revert/{version_number}`** — No request body. Creates a new version that copies the structure from the specified version.

**POST `/api/positions/{id}/rubric/save-as-template`** — Request body:
```json
{
  "name": "New Template Name",
  "description": "Optional"
}
```
Creates a new template from the active version's structure.

**GET `/api/positions/{id}/rubric/versions`** — Response:
```json
{
  "items": [
    { "version_number": 3, "created_by": "Jane Smith", "created_at": "2026-02-16T..." },
    { "version_number": 2, "created_by": "John Doe", "created_at": "2026-02-15T..." },
    { "version_number": 1, "created_by": "Jane Smith", "created_at": "2026-02-14T..." }
  ]
}
```

### Backend Component Breakdown

**New files:**

| File | Responsibility |
|---|---|
| `models/rubric_template.py` | `RubricTemplate` SQLModel |
| `models/position_rubric.py` | `PositionRubric` + `PositionRubricVersion` SQLModels |
| `schemas/rubric_templates.py` | Pydantic schemas for template CRUD |
| `schemas/position_rubrics.py` | Pydantic schemas for position rubric CRUD + versioning |
| `schemas/rubric_structure.py` | Shared pydantic models for JSONB structure validation |
| `services/rubric_template_service.py` | Template CRUD + archive + duplicate logic |
| `services/position_rubric_service.py` | Position rubric CRUD + versioning + revert logic |
| `routers/rubric_templates.py` | `APIRouter(prefix="/api/rubric-templates", tags=["rubric-templates"])` — all routes inject `get_current_user` |
| `routers/position_rubrics.py` | `APIRouter(prefix="/api/positions", tags=["position-rubrics"])` — nested under positions, all routes inject `get_current_user`; passes `current_user.id` to service for `created_by_id` on version creation |

**Shared validation** (`schemas/rubric_structure.py`):
- Pydantic models: `RubricCriterion`, `RubricCategory`, `RubricStructure`
- Validators: category weights sum to 100, criterion weights within each category sum to 100
- At least one category required, each category must have at least one criterion

### Frontend Component Breakdown

**Feature hooks** (`features/rubrics/`):

| Hook | Purpose |
|---|---|
| `use-rubric-templates` | List active templates |
| `use-rubric-template` | Get single template |
| `use-create-rubric-template` | Create template (invalidates list) |
| `use-update-rubric-template` | Update template (invalidates list + detail) |
| `use-duplicate-rubric-template` | Duplicate template (invalidates list) |
| `use-archive-rubric-template` | Archive template (invalidates list) |
| `use-position-rubric` | Get active rubric for a position |
| `use-create-position-rubric` | Create rubric (from template or custom) |
| `use-update-position-rubric` | Update rubric (creates new version) |
| `use-delete-position-rubric` | Delete rubric |
| `use-rubric-versions` | Get version history |
| `use-revert-rubric-version` | Revert to a version |
| `use-save-rubric-as-template` | Save rubric as template |

**Widgets** (`widgets/rubrics/`):

| Widget | Used In | Responsibility |
|---|---|---|
| `rubric-editor` | Template dialogs, position rubric edit | Shared form: category/criteria CRUD, weight validation, reorder buttons. Uses `react-hook-form` with `useFieldArray` for dynamic lists. Zod schema validates structure. |
| `rubric-summary-card` | Position detail page | Shows source, category count, version number. Actions: Edit, Delete, Save as Template, View History. |
| `template-editor-dialog` | Settings page | Dialog wrapping `rubric-editor` for create/edit templates. |
| `assign-rubric-dialog` | Position detail page | Two-option dialog: "Use Template" (dropdown of active templates) or "Create Custom" (opens editor). |
| `version-history-dialog` | Position detail page | Dialog listing versions with date/creator. Click to view read-only structure. "Revert to this version" action. |
| `rubric-template-table` | Settings page | Table of active templates with name, category count, created date, and action buttons (Edit, Duplicate, Archive). |

**Page modifications:**

| File | Change |
|---|---|
| `routes/_authenticated/settings.tsx` | Add "Rubric Templates" section below "Teams" section. Import `RubricTemplateTable` and `TemplateEditorDialog`. |
| `routes/_authenticated/positions/$positionId.tsx` | Add `RubricSummaryCard` (or "Add Rubric" prompt) between `PositionInfoCard` and `PositionCandidatesTable`. |

### Seed Data

4 default templates inserted via Alembic data migration. Each template has 3–4 categories with 2–4 criteria per category. Example structure for "Software Engineer":

| Category (weight) | Criteria |
|---|---|
| Technical Skills (40%) | System Design (30%), Coding Proficiency (40%), Problem Solving (30%) |
| Communication (25%) | Verbal Clarity (50%), Written Communication (50%) |
| Culture & Collaboration (20%) | Team Collaboration (50%), Adaptability (50%) |
| Leadership & Growth (15%) | Initiative (50%), Learning Mindset (50%) |

Similar balanced structures for Product Manager, Designer, and Data Scientist.

---

## 3. Impact and Risk Analysis

**System Dependencies:**
- **Positions**: Position rubrics depend on positions existing. Position deletion should cascade-delete the rubric (`ON DELETE CASCADE` on `position_rubrics.position_id`).
- **Users**: Version history references `created_by_id`. User deletion should not cascade — use `SET NULL` or a soft-delete-only policy for users.
- **Phase 2 Evaluation Pipeline**: The evaluation pipeline will read rubric versions (JSONB) by version ID. This spec ensures the structure is stable and versioned, but the evaluation consumer is out of scope.

**Potential Risks & Mitigations:**

| Risk | Mitigation |
|---|---|
| JSONB structure drift between templates and versions | Shared Pydantic model (`RubricStructure`) validates all JSONB writes. Schema is documented and tested. |
| Weight validation bypass (frontend-only) | Server-side validation in service layer rejects invalid structures with 422. |
| Large JSONB payloads for complex rubrics | Practical limit: even 20 categories × 10 criteria each is ~10KB. No concern. |
| Race condition on version numbering | Use `SELECT MAX(version_number) ... FOR UPDATE` within a transaction when creating new versions. |
| Orphaned templates after archive | Archive is soft-delete. Existing position rubrics keep `source_template_id` for reference but are independent copies. |

---

## 4. Testing Strategy

**Backend:**
- **Unit tests** for weight validation logic (valid sums, invalid sums, edge cases like single category/criterion)
- **Integration tests** per router: full CRUD cycle for templates, full rubric lifecycle for position rubrics (create → edit → version history → revert → delete)
- **Validation tests**: 422 responses for invalid weight sums, missing required fields, duplicate position rubrics (409)
- **Cascade tests**: Verify position deletion cascades to rubric + versions

**Frontend:**
- **Build + lint verification** (`bun run build && bun run lint`) after all frontend changes
- **Manual testing** of rubric editor: add/edit/delete/reorder categories and criteria, verify real-time weight indicators, verify save blocked when invalid

**Integration:**
- Full flow: create template → assign to position → edit position rubric → verify version created → revert → save as template → verify new template exists
