# Tap - Product Current State Review
**Date:** 2026-02-18
**Method:** Full codebase analysis + Playwright visual walkthrough with seeded dev data
**Screenshots:** `context/product/screenshots/` (18 captures)

---

## 1. Operational Status

### Fully Operational (end-to-end working)
- **Auth**: Google OAuth via Cognito, dev-login bypass, 7-day sessions, domain restriction
- **Candidates**: CRUD, search (name/email), filter (stage/position), sort (name/email/date), pagination (20/page)
- **Positions**: CRUD, filter (status/team), archive, hiring manager assignment
- **Pipeline stages**: New > Screening > Technical > Offer > Hired/Rejected with validated transitions
- **Document upload**: CV (PDF/DOCX/MD, 25MB, versioning), Transcript (file + paste, with metadata)
- **Document viewer**: In-app rendering for PDF/DOCX/MD/TXT
- **Decision rubrics**: Templates (CRUD, duplicate, 3 seeded defaults), position assignment, versioning, revert, save-as-template
- **Teams**: CRUD with position-usage protection on delete
- **Rubric Templates**: Management via Settings page with edit/duplicate/delete
- **Infrastructure**: AWS (VPC, ECS, RDS, S3, CloudFront), CI/CD pipelines, Terraform IaC

### Non-Functional / Fake
- **Dashboard**: All 3 cards (Pipeline, Recent Evaluations, Upcoming Interviews) show **hardcoded placeholder data** -- none connected to any API or real data source

### Not Built Yet (roadmap items)
- AI evaluation pipeline (CV analysis, screening summary, technical scoring, recommendations)
- n8n workflow orchestration
- Lever ATS integration (read/write)
- Barley transcript sync
- Candidate feedback generation

---

## 2. Bugs Found During Visual Walkthrough

### BUG: Double `/api/api/` URL prefix (CRITICAL)

**Location:** `app/frontend/src/main.tsx:18` sets `baseURL: "/api"`, but the generated API client URLs already include the `/api/` prefix (e.g., `/api/candidates/{id}/documents` in `types.gen.ts`). This results in requests to `/api/api/candidates/...` which return 404.

**Impact:** Documents tab on candidate detail page and rubric fetch on position detail page fail silently. The UI shows "No documents uploaded" and "No rubric assigned" even if data exists. Console shows repeated `Failed to load resource: 404` errors.

**Evidence:**
- Console errors on candidate detail: `http://localhost:5173/api/api/candidates/1/documents` (404)
- Console errors on position detail: `http://localhost:5173/api/api/positions/1/rubric` (404)

**Fix:** Either remove the `/api` prefix from the generated URLs (change the OpenAPI `servers` config) or remove the `baseURL: "/api"` from `main.tsx` (since the proxy already handles routing). These need to be consistent -- only one should add `/api`.

### BUG: 404 page has no navigation (LOW)
Navigating to a nonexistent URL shows bare "Not Found" text with no sidebar, no "Go Home" button, no navigation at all. User is stranded.

### ISSUE: Missing ARIA descriptions on rubric dialog (LOW)
Console warnings: `Warning: Missing Description or aria-describedby` on rubric assignment dialog. Accessibility gap.

---

## 3. User Journey Analysis

### Complete Journeys (verified via Playwright)

| Journey | Status | Screenshot |
|---------|--------|------------|
| Sign in via dev-login, session persists | OK | `01-login-page.png` |
| View dashboard after login | OK (but fake data) | `02-dashboard-fake-data.png` |
| Browse candidates list with filters/search/sort/pagination | OK | `03-candidates-list.png` |
| View candidate detail (info card, positions, documents section) | OK | `04-candidate-detail.png` |
| Browse positions list with status/team filters | OK | `05-positions-list.png` |
| View position detail (info, rubric, candidates table) | OK | `06-position-detail.png` |
| Assign rubric template to position | OK | `07-assign-rubric-dialog.png`, `08-rubric-template-dropdown.png` |
| View assigned rubric summary | OK | `09-position-with-rubric.png` |
| Edit rubric (categories, criteria, weights, reorder) | OK | `10-rubric-actions-menu.png`, `11-rubric-editor.png` |
| Manage teams and rubric templates in Settings | OK | `12-settings-page.png` |
| Global upload shortcut (sidebar button, type selection) | OK | `13-upload-menu.png` |
| Upload CV wizard (candidate search, file selection) | OK | `14-upload-cv-wizard-step1.png`, `15-upload-cv-candidate-search.png` |
| Create new candidate | OK | `17-new-candidate-dialog.png` |
| Collapsed sidebar view | OK | `18-collapsed-sidebar.png` |

### Broken / Dead-End Journeys

| Gap | Impact | Details |
|-----|--------|---------|
| **Dashboard shows fake data** | CRITICAL | User lands on dashboard after login and sees fabricated pipeline numbers ("Screening 12, Interview 8, Technical 5, Offer 3"), fake evaluations (Alex Rivera, Priya Sharma, etc.), and fake upcoming interviews (Chen Wei, Sam Patel, etc.). None of this data exists in the system. Actively misleading. |
| **Documents don't load (double /api bug)** | CRITICAL | The `/api/api/` prefix bug means documents and rubrics fetched via the auto-generated client silently fail. Users see empty states even when data exists. |
| **Upload documents -- then what?** | HIGH | After uploading CV/transcript, nothing happens. No AI processing, no evaluation, no next step. The workflow dead-ends. |
| **Rubric exists but unused** | MEDIUM | Rubric can be assigned to a position and edited, but there's no scoring UI, no evaluation against it. It's a data structure with no consumer. |
| **No candidate notes/comments** | MEDIUM | No way to add free-form notes about a candidate. Transcript notes exist but are metadata on upload, not editable after. |
| **No hiring manager "my view"** | MEDIUM | HM can't see a filtered view of just their positions and candidates requiring attention. |
| **No candidate comparison** | LOW | No side-by-side comparison of candidates for the same position. |
| **No bulk operations** | LOW | Can't reject/advance multiple candidates at once. |
| **No document download** | LOW | View-only in app. No way to download original file. |
| **No activity log** | LOW | No history of who did what. Stage changes, uploads, edits are not tracked beyond `updated_at` timestamps. |

### Missing User Journeys (not in any spec yet)

1. **"What should I do next?" flow** -- No guidance after core data entry. A new user creates positions and candidates but gets no prompts about uploading documents or setting up rubrics.
2. **Candidate evaluation flow** -- The core value prop (AI-powered evaluation) has zero UI. No evaluation results page, no scoring display, no hire/no-hire recommendation.
3. **Notification/alert flow** -- No notifications for: new candidate added to your position, document uploaded, evaluation complete.
4. **Onboarding flow** -- First-time users see an empty dashboard with fake data and no help text.

---

## 4. UX Assessment

### What Works Well
- **Clean navigation**: Collapsible sidebar with 4 clear sections + global upload button
- **Consistent patterns**: Card-based layout, tables with hover, badge-based status indicators with semantic colors (green=hired/open, red=rejected, etc.)
- **Form handling**: Zod validation, inline errors, disabled state during submission, duplicate detection
- **Empty states**: List pages have icon + message + CTA when empty (though candidate detail documents section says "Upload a CV or transcript to get started" which is good guidance)
- **Loading states**: Skeleton placeholders, spinners, disabled buttons during mutations
- **Error handling**: Conflict errors (duplicate email/team), deletion guards (team with positions)
- **Inline editing**: Candidate/position info cards use pencil-icon edit mode pattern
- **Document upload UX**: Multi-file with per-file validation, progress bars, paste alternative for transcripts
- **Global upload shortcut**: Accessible from any page via sidebar, multi-step wizard with candidate search
- **Stage badges**: Color-coded by pipeline stage (technical=outline, offer=dark, hired=green, rejected=red, new=filled, screening=outline)
- **Rubric editor**: Full-featured with category/criteria nesting, weight validation, drag reorder, totals display

### UX Problems

| Issue | Severity | Details |
|-------|----------|---------|
| **Dashboard is actively misleading** | CRITICAL | Shows "Candidates Pipeline: Screening 12, Interview 8, Technical 5, Offer 3" and "Recent Evaluations" with completion status badges -- all fabricated. Screenshot `02-dashboard-fake-data.png` shows the full extent. A real user will think the system has data it doesn't. |
| **No onboarding or guidance** | HIGH | First-time user logs in -> sees fake dashboard -> clicks Candidates -> empty list -> "New Candidate" button. No explanation of what Tap does, how to get started, or what the workflow is. |
| **404 page is bare** | MEDIUM | Just the text "Not Found" with no sidebar, no navigation, no link back. Screenshot `16-404-page.png`. User is completely stranded. |
| **Rubric editor complexity** | MEDIUM | Weight validation (categories must sum to 100%, criteria within each category must sum to 100%) shown as "Total: 100% / 100%" and "Criteria: 100% / 100%" but no tooltip or help text explains the concept. Users may not understand why save is blocked if totals don't match. |
| **No breadcrumbs** | MEDIUM | Navigating to Candidate Detail from Positions -> Position Detail -> Candidates table loses context. No breadcrumb trail to get back. Browser back button is the only option. |
| **No indication of "completeness"** | MEDIUM | A position with no rubric, no candidates, or candidates with no documents has no visual indicator that setup is incomplete. No progress checklist. |
| **Position card info density** | LOW | Position detail shows info card + rubric card + candidates table. For positions with many candidates (7 for "Senior Backend Engineer"), the page gets very long with no anchoring or section nav. |
| **No keyboard shortcuts** | LOW | Power users (recruiters processing many candidates) have no keyboard navigation for common actions. |

### Accessibility
- Semantic HTML used (buttons, links, form elements, tables with proper row/column structure)
- ARIA labels present on icon-only buttons (e.g., "Rubric actions", "Upload documents")
- Missing: `aria-describedby` on rubric dialog (console warnings)
- No known screen reader testing done
- No dark mode support
- No responsive/mobile design (sidebar is desktop-oriented, collapses to icons but not mobile-friendly)

---

## 5. Screenshot Inventory

| # | File | Page/State |
|---|------|------------|
| 01 | `01-login-page.png` | Login page with Google OAuth + dev-login |
| 02 | `02-dashboard-fake-data.png` | Dashboard with all hardcoded placeholder data |
| 03 | `03-candidates-list.png` | Candidates list with 25 seeded candidates |
| 04 | `04-candidate-detail.png` | Candidate detail (info card, positions, empty documents) |
| 05 | `05-positions-list.png` | Positions list with 10 positions, status badges |
| 06 | `06-position-detail.png` | Position detail (info, no rubric state, candidates) |
| 07 | `07-assign-rubric-dialog.png` | Rubric assignment dialog (Use Template / Create Custom) |
| 08 | `08-rubric-template-dropdown.png` | Template dropdown showing 3 seeded templates |
| 09 | `09-position-with-rubric.png` | Position after rubric assigned (summary: source, categories, author) |
| 10 | `10-rubric-actions-menu.png` | Rubric context menu (Edit, View History, Save as Template, Delete) |
| 11 | `11-rubric-editor.png` | Full rubric editor with 4 categories, criteria, weights |
| 12 | `12-settings-page.png` | Settings: Teams list + Rubric Templates table |
| 13 | `13-upload-menu.png` | Global upload dropdown (Upload CV / Upload Transcript) |
| 14 | `14-upload-cv-wizard-step1.png` | Upload CV wizard: candidate search step |
| 15 | `15-upload-cv-candidate-search.png` | Upload CV: search results dropdown showing match |
| 16 | `16-404-page.png` | 404 page -- bare "Not Found" text, no navigation |
| 17 | `17-new-candidate-dialog.png` | Create Candidate dialog (name + email) |
| 18 | `18-collapsed-sidebar.png` | Collapsed sidebar (icon-only mode) |

---

## 6. Summary & Priority Recommendations

### Current State in One Sentence
Tap is a **solid CRUD foundation** with good UX patterns for data entry and document management, but the **core value proposition (AI-powered candidate evaluation) is entirely unbuilt**, the **dashboard actively misleads users** with fake data, and a **critical URL routing bug** silently breaks document and rubric fetching.

### Priority Recommendations

| # | Action | Severity | Effort |
|---|--------|----------|--------|
| 1 | **Fix the double `/api/api/` URL prefix bug** -- either remove `baseURL: "/api"` from `main.tsx` or change OpenAPI spec to not include `/api` prefix in paths | CRITICAL | Small |
| 2 | **Fix the dashboard** -- replace hardcoded data with real aggregate queries OR replace with an honest "getting started" guide | CRITICAL | Medium |
| 3 | **Fix the 404 page** -- add sidebar, "Go to Dashboard" button, friendly message | LOW | Small |
| 4 | **Add a "getting started" checklist** to empty/new states | HIGH | Medium |
| 5 | **Design the evaluation results UI** (even as mockup/spec) | HIGH | Medium |
| 6 | **Add candidate notes** | MEDIUM | Medium |
| 7 | **Add breadcrumb navigation** | MEDIUM | Small |
| 8 | **Add activity log to candidate detail** | MEDIUM | Medium |
