# Functional Specification: Core Data Management (Candidates, Positions, Candidate List)

- **Roadmap Item:** Web Application (SPA) → Candidate Management + Position Management + Candidate List
- **Status:** Draft
- **Author:** Nail

---

## 1. Overview and Rationale (The "Why")

Tap's POC is manual-first — Lever sync is deferred, so recruiters and hiring managers need to create and manage candidates and positions directly in the web app. This is the foundational CRUD layer that all later features (CV upload, transcript analysis, evaluations, recommendations) depend on.

**Problem:** Without a way to enter and organize candidate and position data, there is nothing to attach uploads, evaluations, or pipeline tracking to. The evaluation pipeline has no subjects.

**Desired outcome:** Recruiters can create positions with requirements, add candidates, associate them with positions, and track each candidate's progress through the hiring pipeline — all within the SPA.

**Success criteria:**
- Users can create, view, edit, and archive candidates and positions
- Each candidate-position pair tracks an independent pipeline stage
- The candidate list supports search and filtering by stage and position
- Data persists across sessions and is shared among all authenticated users

---

## 2. Functional Requirements (The "What")

### 2.1 Candidate Management

#### 2.1.1 Create Candidate

- An authenticated user can create a new candidate by providing:
  - **Full name** (required)
  - **Email address** (required, must be a valid email format)
- On creation, the candidate has no position associations. Positions are linked separately (see 2.1.3).
  - **Acceptance Criteria:**
    - [ ] A "New Candidate" action is available from the Candidate List page
    - [ ] Full name and email are required — form cannot be submitted without them
    - [ ] Email is validated for format (e.g., rejects "not-an-email")
    - [ ] Duplicate email addresses are rejected with a clear error message: *"A candidate with this email already exists."*
    - [ ] After creation, the user is taken to the Candidate Detail page

#### 2.1.2 View & Edit Candidate

- Clicking a candidate in the list opens the **Candidate Detail page** showing:
  - Full name, email
  - List of associated positions with the pipeline stage for each
  - Created date, last modified date
- The user can edit the candidate's name and email inline or via an edit mode.
  - **Acceptance Criteria:**
    - [ ] Candidate Detail page displays all fields listed above
    - [ ] Name and email are editable
    - [ ] Changes are saved explicitly (not auto-saved) — a "Save" action is required
    - [ ] Email uniqueness is enforced on edit (same error as creation)

#### 2.1.3 Associate Candidate with Position(s)

- From the Candidate Detail page, the user can link the candidate to one or more positions.
- When linking to a position, the initial pipeline stage is **New**.
- A candidate can be linked to multiple positions. Each link has its own independent pipeline stage.
- A candidate-position link can be removed.
  - **Acceptance Criteria:**
    - [ ] An "Add to Position" action is available on the Candidate Detail page
    - [ ] User selects from a list of existing positions (only non-archived positions shown)
    - [ ] The same candidate cannot be linked to the same position twice — duplicate attempt shows: *"Candidate is already associated with this position."*
    - [ ] Each candidate-position link shows the current pipeline stage
    - [ ] Removing a link requires confirmation: *"Remove [candidate] from [position]? This will delete their pipeline progress for this position."*

#### 2.1.4 Pipeline Stage Tracking

- Each candidate-position pair has a pipeline stage: **New → Screening → Technical → Offer → Hired** or **Rejected**.
- The stage can be changed manually by the user from the Candidate Detail page.
- "Rejected" is a terminal stage that can be set from any prior stage.
- "Hired" is a terminal stage that can only be set from "Offer."
  - **Acceptance Criteria:**
    - [ ] The current stage is displayed for each candidate-position pair
    - [ ] Stage can be advanced forward (New → Screening → Technical → Offer → Hired)
    - [ ] Stage can be set to "Rejected" from any non-terminal stage
    - [ ] Stage cannot be moved backward (e.g., Technical → Screening is not allowed)
    - [ ] Changing stage requires a single click/action (no multi-step confirmation)

#### 2.1.5 Archive Candidate

- A candidate can be archived (soft deleted). Archived candidates are hidden from the default Candidate List view.
- Archiving does not delete associated data — it can be restored later if needed.
  - **Acceptance Criteria:**
    - [ ] An "Archive" action is available on the Candidate Detail page
    - [ ] Archiving requires confirmation: *"Archive [candidate name]? They will be hidden from the candidate list."*
    - [ ] Archived candidates do not appear in the default Candidate List
    - [ ] [NEEDS CLARIFICATION: Should there be a way to view/restore archived candidates in the POC, or is that deferred?]

### 2.2 Position Management

#### 2.2.1 Create Position

- An authenticated user can create a new position by providing:
  - **Title** (required) — e.g., "Senior Backend Engineer"
  - **Requirements** (optional) — free text describing role requirements
  - **Team** (required) — selected from a predefined, editable dropdown (see 2.4)
  - **Hiring Manager** (required) — selected from the list of Tap users (authenticated Provectus employees who have logged in at least once)
  - **Status** — defaults to **Open** on creation
  - **Acceptance Criteria:**
    - [ ] A "New Position" action is available from the Position List page
    - [ ] Title, team, and hiring manager are required
    - [ ] Team is selected from a dropdown populated by the editable team list
    - [ ] Hiring manager is selected from a dropdown of existing Tap users
    - [ ] Requirements field accepts multi-line free text
    - [ ] Status defaults to "Open" and cannot be changed during creation
    - [ ] After creation, the user is taken to the Position Detail page

#### 2.2.2 Position List Page

- A dedicated page listing all positions.
- Displays: title, team, hiring manager name, status, number of active candidates.
- Positions are filterable by status (Open / On Hold / Closed) and by team.
- Archived positions are hidden from the default view.
  - **Acceptance Criteria:**
    - [ ] Position List page is accessible from main navigation
    - [ ] Each row shows: title, team, hiring manager, status, candidate count
    - [ ] User can filter by status (Open / On Hold / Closed / All)
    - [ ] User can filter by team
    - [ ] Clicking a position navigates to the Position Detail page

#### 2.2.3 View & Edit Position

- Clicking a position opens a **Position Detail page** showing all fields plus a list of associated candidates with their pipeline stages.
- All fields (title, requirements, team, hiring manager, status) are editable.
  - **Acceptance Criteria:**
    - [ ] Position Detail page displays all fields and associated candidates
    - [ ] All fields are editable
    - [ ] Status can be changed to Open, On Hold, or Closed
    - [ ] Changes are saved explicitly via a "Save" action

#### 2.2.4 Archive Position

- A position can be archived (soft deleted). Archived positions are hidden from the default Position List and from position dropdowns when linking candidates.
  - **Acceptance Criteria:**
    - [ ] An "Archive" action is available on the Position Detail page
    - [ ] Archiving requires confirmation
    - [ ] Archived positions do not appear in the default list or in candidate-position linking dropdowns
    - [ ] Candidates already linked to an archived position retain their data

### 2.3 Candidate List Page

- A dedicated page listing all candidates (the primary navigation entry point).
- Displays a table with columns: **Name, Email, Position(s), Stage, Last Updated**.
- If a candidate is linked to multiple positions, each position-stage pair is shown (e.g., "Backend Engineer: Screening, Frontend Lead: Technical").

#### 2.3.1 Search

- A search bar filters candidates by name or email as the user types.
  - **Acceptance Criteria:**
    - [ ] Search input is visible at the top of the candidate list
    - [ ] Typing filters results in real-time (client-side for POC, or debounced API call)
    - [ ] Search matches against candidate name and email (case-insensitive, partial match)
    - [ ] Clearing the search restores the full list

#### 2.3.2 Filters

- Filter by **pipeline stage**: show candidates who are at a specific stage for any of their positions.
- Filter by **position**: show only candidates linked to a specific position.
- Filters can be combined (e.g., "Screening" + "Backend Engineer" = candidates at Screening stage for the Backend Engineer position).
  - **Acceptance Criteria:**
    - [ ] Stage filter dropdown with options: All, New, Screening, Technical, Offer, Hired, Rejected
    - [ ] Position filter dropdown populated by non-archived positions
    - [ ] Filters can be combined
    - [ ] Active filters are visually indicated
    - [ ] A "Clear filters" action resets all filters

#### 2.3.3 Sorting

- The list is sorted by **last updated** (most recent first) by default.
- Column headers are clickable to sort by that column.
  - **Acceptance Criteria:**
    - [ ] Default sort: last updated, descending
    - [ ] Clicking a column header sorts by that column
    - [ ] Sort direction toggles on repeated clicks (asc/desc)

### 2.4 Team Management (Settings)

- A **Settings** page accessible from the main navigation or user menu.
- The Settings page includes a **Teams** section where users can:
  - View the list of existing teams
  - Add a new team (text input)
  - Remove a team (only if no positions are currently using it)
  - **Acceptance Criteria:**
    - [ ] Settings page is accessible from the navigation
    - [ ] Teams section lists all existing teams
    - [ ] User can add a new team by typing a name and confirming
    - [ ] Duplicate team names are rejected
    - [ ] Removing a team that is in use by any position (including archived) is blocked with a message: *"This team is assigned to [N] position(s) and cannot be removed."*
    - [ ] Removing an unused team requires confirmation

---

## 3. Scope and Boundaries

### In-Scope

- Candidate CRUD (create, view, edit, archive) with name + email
- Position CRUD (create, view, edit, archive) with title, requirements, team, hiring manager, status
- Many-to-many candidate-position association with independent pipeline stage tracking
- Pipeline stages: New → Screening → Technical → Offer → Hired/Rejected (forward-only + reject from any)
- Candidate List page with search, stage filter, position filter, and sortable columns
- Position List page with status and team filters
- Candidate Detail page and Position Detail page
- Team management via Settings page (add/remove teams)
- Hiring manager dropdown populated from existing Tap users

### Out-of-Scope

- **The following are separate roadmap items and will be addressed in their own specs:**
  - Interview Library & Recording/Transcript Viewer
  - CV Upload & Transcript Upload
  - Backend API implementation details (endpoints, data models — covered in tech spec)
  - n8n Integration & workflows
  - Barley Integration (S3 transcript sync)
  - Lever Integration (read/write)
  - CV Analysis, Screening Summary, Technical Evaluation, Recommendation Generation (Phase 2)
  - Candidate Feedback Generation (Phase 3)
- **Deferred features within this domain:**
  - Role-based access control (all users can do everything)
  - Bulk operations (import, bulk stage change)
  - Candidate notes / activity log
  - Viewing / restoring archived records [NEEDS CLARIFICATION]
  - Position description rich text formatting (plain text for POC)
