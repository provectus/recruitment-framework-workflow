# Functional Specification: Decision Rubric Management

- **Roadmap Item:** Decision Rubric Engine — Apply weighted scoring framework, generate recommendation with clear reasoning
- **Status:** Completed
- **Author:** Claude (AI-assisted)

---

## 1. Overview and Rationale (The "Why")

**Problem:** Today, hiring managers evaluate candidates against free-text position requirements with no structured scoring criteria. Evaluation quality depends entirely on individual judgment, making it inconsistent across interviewers and positions. When the AI evaluation pipeline (Phase 2) processes interview transcripts, it has no structured framework to score against — only narrative requirements text.

**Solution:** A rubric management system that lets users define weighted evaluation criteria organized into categories and individual scoring criteria. Rubrics serve as the structured backbone for both human and AI-powered evaluation.

**Desired Outcome:**
- Every position *can* have a structured rubric defining exactly what to evaluate and how to weight it
- Rubrics are reusable via a template library, reducing setup effort for similar roles
- The evaluation pipeline (Phase 2) can consume rubric structure to produce criterion-level scores with transparent reasoning

**Success Metrics:**
- Positions with assigned rubrics before candidates reach the evaluation stage
- Reduction in time to set up evaluation criteria for new positions (via template reuse)
- Rubric structure consumed successfully by the AI evaluation pipeline (Phase 2 dependency)

---

## 2. Functional Requirements (The "What")

### 2.1 Rubric Structure

A rubric defines **what to evaluate** and **how to weight it**. It has two levels:

```
Rubric
├── Category A (weight: 40%)
│   ├── Criterion A1 (weight: 50% of category)
│   ├── Criterion A2 (weight: 30%)
│   └── Criterion A3 (weight: 20%)
├── Category B (weight: 35%)
│   ├── Criterion B1 (weight: 60%)
│   └── Criterion B2 (weight: 40%)
└── Category C (weight: 25%)
    └── Criterion C1 (weight: 100%)
```

- **Category:** A broad evaluation area (e.g., "Technical Skills", "Communication"). Has a name (required), description (optional), and weight as a percentage of the total rubric.
- **Criterion:** A specific evaluation item within a category (e.g., "System Design", "Written Communication"). Has a name (required), description (optional), and weight as a percentage of its parent category.
- **Scoring scale:** Fixed 1–5 scale used during evaluation (not part of this spec, but the rubric defines what gets scored):
  1. Strong No
  2. No
  3. Neutral
  4. Yes
  5. Strong Yes

**Acceptance Criteria:**
- [x] A rubric contains one or more categories, each containing one or more criteria
- [x] Each category has a name (required), description (optional), and weight percentage
- [x] Each criterion has a name (required), description (optional), and weight percentage
- [x] No hard limits on the number of categories or criteria

### 2.2 Weight Validation

Weights must be mathematically valid before a rubric can be saved.

- Category weights within a rubric must sum to exactly **100%**
- Criterion weights within each category must sum to exactly **100%**
- The editor shows a real-time indicator (e.g., "75% / 100%") for each level as the user edits
- Save is **blocked** with a clear inline error when weights are invalid

**Acceptance Criteria:**
- [x] When category weights sum to less than or greater than 100%, a validation error is shown and save is disabled
- [x] When criterion weights within any category sum to less than or greater than 100%, a validation error is shown and save is disabled
- [x] The user sees a real-time weight total indicator per rubric level (categories, and within each category)
- [x] Save button is disabled with an explanatory message when validation fails

### 2.3 Template Library

Templates are reusable rubric definitions managed from the **Settings** page. Any logged-in user can create, edit, duplicate, and archive templates.

**Viewing templates:**
- The Settings page has a "Rubric Templates" section showing all active templates in a table
- Each row shows: template name, number of categories, created date, and actions
- Archived templates are hidden from the list by default

**Creating a template:**
- User clicks "Create Template" to open an editor dialog
- User enters template name, optional description, then builds the rubric structure (categories + criteria + weights)
- Save creates the template (blocked if weights are invalid)

**Editing a template:**
- User clicks "Edit" on a template row to open the editor dialog pre-filled with the current structure
- Edits are saved in-place (templates do not have version history — only position rubrics do)

**Duplicating a template:**
- User clicks "Duplicate" on a template row
- A copy is created with the name "[Original Name] (Copy)"
- The copy opens in the editor for immediate customization

**Archiving a template:**
- User clicks "Archive" on a template row
- If any position rubrics were originally cloned from this template, a warning is shown: "X positions were created from this template. Archiving will not affect existing position rubrics."
- User confirms to archive
- Archived templates disappear from the active list and from the "clone from template" selection
- Archiving does NOT affect position rubrics that were previously cloned from it (they are independent copies)

**Default templates:**
- The system is seeded with 4 default templates: Software Engineer, Product Manager, Designer, Data Scientist
- Default templates are fully editable — they behave like any other template
- Each contains 3–4 categories with 2–4 criteria per category

**Acceptance Criteria:**
- [x] Settings page shows a "Rubric Templates" section with a table of active templates
- [x] User can create a new template with name, description, categories, and criteria
- [x] User can edit any existing template (including default ones)
- [x] User can duplicate a template, creating a copy with "(Copy)" suffix
- [x] Archiving shows a warning with the count of positions that cloned from this template
- [x] Archived templates are hidden from the template list and template selection dialogs
- [x] 4 default templates are available on fresh system setup
- [x] Template changes do not retroactively affect position rubrics cloned from them

### 2.4 Position Rubrics

Each position can have **zero or one active rubric**. A rubric is optional for general position management but will be required for AI-powered evaluation (Phase 2).

**When no rubric exists:**
- The position detail page shows an "Add Rubric" prompt within a summary card area
- Clicking opens the "Assign Rubric" dialog with two options:
  - **Use Template:** Select from the active template library → clones it as the position's rubric
  - **Create Custom:** Opens a blank rubric editor

**When a rubric exists:**
- The position detail page shows a **summary card** with: rubric source (template name or "Custom"), category count, current version number
- Available actions: **Edit**, **Delete**, **Save as Template**, **View History**

**Editing a position rubric:**
- Opens the rubric editor pre-filled with the current active version
- Saving creates a **new version** (see §2.5 Versioning)

**Deleting a position rubric:**
- Confirmation dialog: "Remove rubric from [Position Name]? All versions will be deleted."
- Removes the rubric entirely (all versions)

**Save as Template:**
- Creates a new template from the current active rubric version
- User provides a template name → template appears in the template library

**Acceptance Criteria:**
- [x] Position detail page shows "Add Rubric" when no rubric is assigned
- [x] User can assign a rubric by cloning from a template or creating custom
- [x] Cloning from a template creates an independent copy (not linked to template)
- [x] Position detail page shows a summary card when a rubric exists (source, category count, version)
- [x] User can edit, delete, or save the rubric as a new template
- [x] Deleting a rubric removes all versions and shows a confirmation dialog
- [x] Saving a position rubric as a template creates a new entry in the template library

### 2.5 Rubric Versioning

Position rubrics support explicit versioning. Every save creates a new version, preserving the history.

**Creating a new version:**
- When a user edits and saves a position rubric, the save creates a new version (v2, v3, etc.)
- The previous version is preserved as read-only
- The newly saved version becomes the active version

**Viewing history:**
- "View History" action on the position rubric card opens a version list
- Each entry shows: version number, date created, who created it
- Clicking a version shows the full rubric structure (read-only)

**Reverting to a previous version:**
- From the version history, user can click "Revert to this version"
- Reverting creates a **new version** that is a copy of the selected past version (does not delete intermediate versions)
- Example: v1 → v2 → v3 → revert to v1 → creates v4 (which is a copy of v1's structure)

**Evaluation reference:**
- When candidates are evaluated against a rubric (Phase 2), the evaluation records which version was used
- This is out of scope for this spec but informs why version history matters

**Acceptance Criteria:**
- [x] Every edit-and-save on a position rubric creates a new version
- [x] Previous versions are preserved and viewable as read-only
- [x] Version history shows version number, creation date, and creator
- [x] User can revert to any previous version, which creates a new version (copy)
- [x] Reverting does not delete any intermediate versions
- [x] The active version is always the latest version

### 2.6 Rubric Editor (Shared Component)

The rubric editor is used for both template editing and position rubric editing. It uses simple form controls.

**Category management:**
- Add a new category (name input, optional description, weight input)
- Edit existing category name, description, and weight
- Delete a category (with confirmation if it has criteria)
- Reorder categories using up/down arrow buttons

**Criterion management (within a category):**
- Add a new criterion (name input, optional description, weight input)
- Edit existing criterion name, description, and weight
- Delete a criterion
- Reorder criteria using up/down arrow buttons

**Validation display:**
- Real-time weight total shown per level (e.g., "75% / 100%")
- Invalid totals highlighted in red
- Save button disabled with tooltip explaining which level is invalid

**Acceptance Criteria:**
- [x] User can add, edit, delete, and reorder categories
- [x] User can add, edit, delete, and reorder criteria within each category
- [x] Reordering uses up/down arrow buttons (no drag-and-drop)
- [x] Weight validation is shown in real-time at both levels
- [x] Save is blocked when weights are invalid, with a clear error message
- [x] Deleting a category with criteria shows a confirmation dialog

---

## 3. Scope and Boundaries

### In-Scope
- Rubric data structure (categories → criteria with weights)
- Template library CRUD (create, read, update, archive, duplicate)
- Position rubric assignment (from template or custom)
- Position rubric editing, deletion, and save-as-template
- Rubric versioning (explicit versions, view history, revert)
- Rubric editor widget (form-based, up/down reorder, weight validation)
- 4 seeded default templates
- Weight validation (block save when invalid)
- Summary card on position detail page
- Settings page section for template management

### Out-of-Scope
- **AI-assisted rubric generation** (e.g., "generate rubric from requirements text") — future enhancement
- **Scoring/evaluation against rubrics** — Phase 2: Technical Evaluation
- **n8n workflow integration** for rubric-based evaluation — Phase 2
- **Lever integration** for rubric data — Future phase
- **Barley integration** — Phase 1 separate item
- **Interview Library** — Phase 1 separate item
- **CV Analysis** — Phase 1 separate item
- **Screening Summary / HM Review** — Phase 2 separate items
- **Candidate Feedback Generation** — Phase 3 separate item
- **Permission/role-based access control** — no role restrictions for MVP; any logged-in user can manage all rubrics and templates
- **Drag-and-drop reordering** — using up/down arrows instead
- **Rubric import/export** (e.g., CSV, JSON)
- **Rubric comparison** (side-by-side version diff)
