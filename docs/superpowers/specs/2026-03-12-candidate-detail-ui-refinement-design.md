# Candidate Detail Page UI Refinement

## Context

The candidate detail page (`/candidates/$candidateId`) displays evaluation pipeline results from 5 AI-powered steps. After running the pipeline, the page becomes an extremely long vertical scroll with all evaluation results expanded inline. Recruiters struggle to find actionable information (recommendation, key scores) buried at the bottom.

**Pain points addressed:**
- Information overload — all 5 evaluation results expanded simultaneously
- Layout hierarchy — recommendation/verdict buried below thousands of pixels of detail
- Visual polish — evaluation tables and text blocks are dense and utilitarian

## Design

### Section 1: Summary Banner

**Placement:** Between candidate header (name + email) and Candidate Info Card.

**Layout:** Single horizontal strip, ~48-56px content height, subtle background tint (not a heavy card border).

**Content (left to right):**
- Recommendation verdict badge (`Hire` green / `No Hire` red / `Needs Discussion` amber) + confidence badge (`High` / `Medium` / `Low`)
- Technical evaluation score (`X.X / 5.0` with small inline progress bar; denominator is hardcoded `5` — same constant used in `technical-eval-result.tsx`)
- Pipeline progress — 5 step indicators, one per entry in `STEP_ORDER`. Always render all 5 regardless of whether the API has returned a record for each. Steps without an API record render as "not started" (grey).

**Data sourcing:** The banner component receives `evaluations: EvaluationResponse[]` and builds a `stepMap` keyed by `step_name` (same pattern as `evaluation-results.tsx`). It reads:
- `stepMap.recommendation?.result?.recommendation` + `result?.confidence` for verdict/confidence badges
- `stepMap.recommendation?.result?.reasoning` (first sentence, max 150 chars) for the one-liner
- `stepMap.technical_eval?.result?.weighted_total` for the technical score
- Each step's `status` field for pipeline progress indicators

**Below the metric row:** One line of muted text — first sentence of the recommendation reasoning, truncated at 150 characters. E.g., *"Strong application-layer skills, gaps in CI/CD and Docker may require ramp-up"*

**Edge cases:**
- No evaluations run → muted "No evaluations yet" state (banner still visible)
- Pipeline partially complete → show available metrics, grey out unavailable ones with muted placeholder text
- Pipeline failed mid-way → show last successful data + red failed indicator on the failed step
- `result` is `null` for a step (running or failed) → treat metrics from that step as unavailable

### Section 2: Accordion Evaluation Steps

Replace the current always-expanded evaluation step cards with accordion panels. All collapsed by default. Multiple can be open simultaneously.

**Collapsed row structure:** `[Status Badge]  Step Name  ·  Key Metric  ·  One-liner summary  [Re-run] [History]`

Re-run and History buttons are always visible in the accordion header (right-aligned), not hidden inside expanded content.

**Per-step summary content:**

| Step | Key Metric | One-liner Source |
|---|---|---|
| CV Analysis | `X/Y skills present` (count where `skills_match[].present === true` / total) | First sentence of `overall_fit` field (split on `.`, take first, max 120 chars) |
| Screening Evaluation | First item from `strengths[]` (or `—` if empty) | First item from `key_topics[]` |
| Technical Evaluation | `X.X / 5.0` (`weighted_total / 5`) | First item from `strengths_summary[]` |
| Recommendation | `Verdict · Confidence` (`recommendation` + `confidence`) | First sentence of `reasoning` field (max 120 chars) |
| Feedback Draft | `Stage: <rejection_stage>` | First sentence of `feedback_text` (max 120 chars) |

When `result` is `null` (step pending/running/failed), the key metric and one-liner show `—` placeholders.

**Expanded content:** Same as current, with one structural change — for all steps, summary/highlight text appears *above* tables and score grids:
- CV Analysis: Overall Fit paragraph renders first, above Skills Match table (currently renders last in `cv-analysis-result.tsx`)
- Screening: Key Topics + Strengths above Concerns/Communication/Motivation
- Technical: Strengths + Improvement Areas above Criteria Scores table (currently renders below)
- Recommendation: Reasoning above any detail
- Feedback: Feedback text (no reordering needed)

**`HmDecisionGate` placement:** `HmDecisionGate` renders as a non-accordion row *between* accordion items, in the same positions as today (after `screening_eval`, after `recommendation`). It is a sibling to accordion items, not nested inside any accordion panel.

**Accordion state:** Local React state (`useState<Set<string>>`), not persisted. Switching position tabs (when candidate has multiple positions) resets all accordion panels to collapsed.

**Accordion behavior:**
- Click header row to toggle open/close
- Multiple can be open simultaneously
- Smooth height animation on expand/collapse (use shadcn `Collapsible` or CSS `grid-template-rows` transition)

### Section 3: Inline Tabbed Transcripts

Remove the dialog-based transcript viewer for transcripts. Render transcripts inline within the Documents card.

**Structure:**
- Tabs labeled by interview stage name: e.g., `Screening` | `Technical`
- When multiple transcripts share the same stage, append the interview date: e.g., `Screening – Mar 5`. If no date is available, append a numeric suffix: `Screening (1)`, `Screening (2)`
- Tab content: transcript rendered inline using extracted rendering logic (see "Shared extraction" below)
- Compact metadata header above text: interviewer name, interview date, notes (if any)
- Max height: ~500px with internal scroll (`overflow-y-auto`)
- If only one transcript exists, render it directly without tabs

**Data fetching:** Lazy-load transcript content on first tab activation (consistent with the existing dialog pattern). Each tab uses `useDocument(documentId)` (which handles presigned URL fetching via React Query cache). Show a loading skeleton inside the tab content area while fetching. React Query's stale-while-revalidate handles presigned URL expiry naturally.

**CVs remain in dialog:** PDF and docx CVs continue using the existing DocumentViewer dialog — they don't inline well and benefit from focused viewing.

**Document table changes:** Transcript rows in the document table get a visual indicator (e.g., subtle "View inline" text or eye icon) that clicking scrolls to/activates the corresponding tab in the inline viewer rather than opening a dialog.

### Section 4: Evaluation Result Visual Polish

Targeted improvements to dense evaluation content:

**Skills Match table (CV Analysis):**
- Tighter row height (reduce vertical padding)
- Smaller pill-shaped Present/Absent badges
- Notes column: truncated by default with expandable tooltip or "Show more" toggle
- Consider two-column layout: Present skills left, Absent skills right

**Criteria Scores table (Technical Evaluation):**
- Score column: colored indicator (green >=4, amber 3, red <=2) with `X/5` text
- Evidence and Reasoning columns: collapsed by default, expand on row click or "Show" toggle
- Category grouping: subtle background tint or separator rows between categories
- Weight column: smaller, muted text

**Text blocks (Experience Relevance, Overall Fit, Reasoning, etc.):**
- Slightly smaller font size for body text
- Better paragraph spacing
- Muted uppercase section labels (already present, keep consistent)

**Strengths / Improvement Areas (Technical Evaluation):**
- Side-by-side layout (already exists) — add subtle green-tinted background for strengths, amber-tinted for improvements
- Bullet points with tighter spacing

## Shared Extraction

Extract reusable rendering logic from `DocumentViewer` for use by both the dialog and the new inline transcript viewer:

- **`useDocumentContent(documentId: number, enabled: boolean)`** — new hook at `src/features/documents/hooks/use-document-content.ts`. Encapsulates the fetch + content-state machine (`idle | loading | success | error`) currently inside `DocumentViewer`. Returns `{ content: string | null, contentType: string, state: ContentState }`.
- **`DocumentContentRenderer`** — new component at `src/widgets/documents/document-content-renderer.tsx`. Accepts `{ contentType: string, content: string }` and renders the three non-PDF paths (markdown via ReactMarkdown, plain text via `<pre>`, docx via mammoth + DOMPurify). Both `DocumentViewer` and `InlineTranscriptViewer` consume these.

## Files to Modify

| File | Change |
|---|---|
| `src/routes/_authenticated/candidates/$candidateId.tsx` | Add summary banner between header and info card |
| `src/widgets/evaluations/evaluation-results.tsx` | Refactor to accordion pattern; keep `HmDecisionGate` as sibling rows between accordion items |
| `src/widgets/evaluations/evaluation-step-card.tsx` | Convert to collapsible accordion with summary row header |
| `src/widgets/evaluations/hm-decision-gate.tsx` | No changes needed — renders as-is between accordion items |
| `src/widgets/evaluations/results/cv-analysis-result.tsx` | Reorder: Overall Fit above Skills Match table; polish table styles |
| `src/widgets/evaluations/results/screening-eval-result.tsx` | Reorder: Key Topics + Strengths above other sections |
| `src/widgets/evaluations/results/technical-eval-result.tsx` | Reorder: Strengths + Improvements above Criteria Scores; polish table |
| `src/widgets/documents/document-list.tsx` | Add inline transcript tabbed viewer below the document table |
| `src/widgets/documents/document-viewer.tsx` | Extract content rendering logic into shared hook + component; keep for CV viewing |
| NEW: `src/widgets/evaluations/evaluation-summary-banner.tsx` | Summary banner component |
| NEW: `src/widgets/documents/inline-transcript-viewer.tsx` | Inline tabbed transcript panel |
| NEW: `src/widgets/documents/document-content-renderer.tsx` | Shared content rendering component (markdown, plain text, docx) |
| NEW: `src/features/documents/hooks/use-document-content.ts` | Shared hook for document content fetching + state machine |

## Out of Scope

- HM decision buttons in the summary banner (future — needs Slack/notification integration)
- Two-column or dashboard layout (future evolution)
- Document viewer changes for CVs (stays as dialog)
- Mobile responsiveness (not a current requirement)
