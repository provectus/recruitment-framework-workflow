# Candidate Detail UI Refinement Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce information overload on the candidate detail page by adding a summary banner, collapsible accordion evaluation steps, inline tabbed transcripts, and visual polish to evaluation results.

**Architecture:** Refactor the existing evaluation step cards into Radix Collapsible-based accordions with summary headers. Add a new summary banner component above the info card. Extract document content rendering for reuse between the existing dialog viewer and a new inline transcript panel.

**Tech Stack:** React 19, TypeScript, Radix Collapsible (already installed via shadcn), TanStack Query, Tailwind v4, shadcn/ui components.

**Spec:** `docs/superpowers/specs/2026-03-12-candidate-detail-ui-refinement-design.md`

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `src/shared/lib/evaluation-summary.ts` | CREATE | Pure helper functions to extract summary metrics from evaluation results (skill counts, first sentence, etc.) |
| `src/widgets/evaluations/evaluation-summary-banner.tsx` | CREATE | Summary banner: verdict + score + pipeline progress + one-liner |
| `src/widgets/evaluations/evaluation-step-card.tsx` | MODIFY | Convert to Collapsible accordion with summary header row |
| `src/widgets/evaluations/evaluation-results.tsx` | MODIFY | Add accordion state management, pass open/toggle to step cards |
| `src/widgets/evaluations/cv-analysis-result.tsx` | MODIFY | Reorder: Overall Fit above Skills Match; polish table |
| `src/widgets/evaluations/technical-eval-result.tsx` | MODIFY | Reorder: Strengths above Criteria Scores; polish table |
| `src/widgets/evaluations/screening-eval-result.tsx` | MODIFY | Reorder: Key Topics + Strengths above other sections |
| `src/features/documents/hooks/use-document-content.ts` | CREATE | Shared hook for document content fetching + state machine |
| `src/widgets/documents/document-content-renderer.tsx` | CREATE | Shared content rendering (markdown, plain text, docx) |
| `src/widgets/documents/document-viewer.tsx` | MODIFY | Refactor to use shared hook + renderer |
| `src/widgets/documents/inline-transcript-viewer.tsx` | CREATE | Inline tabbed transcript panel |
| `src/widgets/documents/document-list.tsx` | MODIFY | Integrate inline transcript viewer below document table |
| `src/routes/_authenticated/candidates/$candidateId.tsx` | MODIFY | Add summary banner, wire up inline transcripts |
| `src/widgets/evaluations/index.ts` | MODIFY | Export new `EvaluationSummaryBanner` |
| `src/widgets/documents/index.ts` | MODIFY | Export new `InlineTranscriptViewer`, `DocumentContentRenderer` |

---

## Chunk 1: Summary Helpers + Banner

### Task 1: Create evaluation summary helper functions

**Files:**
- Create: `src/shared/lib/evaluation-summary.ts`

These are pure functions with no React dependencies — easy to test and reuse across the banner and accordion headers.

- [ ] **Step 1: Create the helper file with all summary extraction functions**

```ts
// src/shared/lib/evaluation-summary.ts

import type { EvaluationResponse } from "@/shared/api";

export const STEP_ORDER = [
  "cv_analysis",
  "screening_eval",
  "technical_eval",
  "recommendation",
  "feedback_gen",
] as const;

export type StepType = (typeof STEP_ORDER)[number];

export type StepMap = Partial<Record<StepType, EvaluationResponse>>;

export function buildStepMap(evaluations: EvaluationResponse[]): StepMap {
  const map: StepMap = {};
  for (const ev of evaluations) {
    const step = ev.step_type as StepType;
    if (STEP_ORDER.includes(step)) {
      const existing = map[step];
      if (!existing || ev.version > existing.version) {
        map[step] = ev;
      }
    }
  }
  return map;
}

export function firstSentence(text: string | undefined | null, maxLen = 120): string {
  if (!text) return "—";
  const dot = text.indexOf(".");
  const sentence = dot > 0 ? text.slice(0, dot + 1) : text;
  return sentence.length > maxLen ? sentence.slice(0, maxLen) + "…" : sentence;
}

interface CvSummary {
  metric: string;
  oneLiner: string;
}

export function getCvAnalysisSummary(result: Record<string, unknown> | null): CvSummary {
  if (!result) return { metric: "—", oneLiner: "—" };
  const skills = result.skills_match as Array<{ present: boolean }> | undefined;
  const present = skills?.filter((s) => s.present).length ?? 0;
  const total = skills?.length ?? 0;
  return {
    metric: `${present}/${total} skills`,
    oneLiner: firstSentence(result.overall_fit as string),
  };
}

interface ScreeningSummary {
  metric: string;
  oneLiner: string;
}

export function getScreeningSummary(result: Record<string, unknown> | null): ScreeningSummary {
  if (!result) return { metric: "—", oneLiner: "—" };
  const strengths = result.strengths as string[] | undefined;
  const topics = result.key_topics as string[] | undefined;
  return {
    metric: strengths?.[0] ?? "—",
    oneLiner: topics?.[0] ?? "—",
  };
}

interface TechnicalSummary {
  metric: string;
  score: number | null;
  maxScore: number;
  oneLiner: string;
}

export function getTechnicalSummary(result: Record<string, unknown> | null): TechnicalSummary {
  if (!result) return { metric: "—", score: null, maxScore: 5, oneLiner: "—" };
  const score = result.weighted_total as number | undefined;
  const strengths = result.strengths_summary as string[] | undefined;
  return {
    metric: score != null ? `${score.toFixed(1)} / 5.0` : "—",
    score: score ?? null,
    maxScore: 5,
    oneLiner: strengths?.[0] ?? "—",
  };
}

interface RecommendationSummary {
  metric: string;
  verdict: string | null;
  confidence: string | null;
  oneLiner: string;
}

export function getRecommendationSummary(result: Record<string, unknown> | null): RecommendationSummary {
  if (!result) return { metric: "—", verdict: null, confidence: null, oneLiner: "—" };
  const verdict = result.recommendation as string | undefined;
  const confidence = result.confidence as string | undefined;
  const verdictLabel = verdict?.replace(/_/g, " ") ?? "—";
  const confLabel = confidence ?? "";
  return {
    metric: confLabel ? `${verdictLabel} · ${confLabel}` : verdictLabel,
    verdict: verdict ?? null,
    confidence: confidence ?? null,
    oneLiner: firstSentence(result.reasoning as string, 150),
  };
}

interface FeedbackSummary {
  metric: string;
  oneLiner: string;
}

export function getFeedbackSummary(result: Record<string, unknown> | null): FeedbackSummary {
  if (!result) return { metric: "—", oneLiner: "—" };
  const stage = result.rejection_stage as string | undefined;
  return {
    metric: stage ? `Stage: ${stage}` : "—",
    oneLiner: firstSentence(result.feedback_text as string),
  };
}

export function getStepSummary(stepType: string, result: Record<string, unknown> | null) {
  switch (stepType) {
    case "cv_analysis":
      return getCvAnalysisSummary(result);
    case "screening_eval":
      return getScreeningSummary(result);
    case "technical_eval":
      return getTechnicalSummary(result);
    case "recommendation":
      return getRecommendationSummary(result);
    case "feedback_gen":
      return getFeedbackSummary(result);
    default:
      return { metric: "—", oneLiner: "—" };
  }
}
```

- [ ] **Step 2: Verify it compiles**

Run: `cd app/frontend && npx tsc --noEmit --pretty 2>&1 | head -20`
Expected: No errors related to `evaluation-summary.ts`

- [ ] **Step 3: Commit**

```bash
git add app/frontend/src/shared/lib/evaluation-summary.ts
git commit -m "feat(frontend): add evaluation summary helper functions"
```

---

### Task 2: Create EvaluationSummaryBanner component

**Files:**
- Create: `src/widgets/evaluations/evaluation-summary-banner.tsx`
- Modify: `src/widgets/evaluations/index.ts` (add export)

- [ ] **Step 1: Create the banner component**

```tsx
// src/widgets/evaluations/evaluation-summary-banner.tsx

import { Badge } from "@/shared/ui/badge";
import { Progress } from "@/shared/ui/progress";
import type { EvaluationResponse } from "@/shared/api";
import {
  buildStepMap,
  getRecommendationSummary,
  getTechnicalSummary,
  STEP_ORDER,
} from "@/shared/lib/evaluation-summary";
import {
  getEvaluationStepLabel,
  formatEvaluationStatus,
} from "@/shared/lib/evaluation-utils";
import { cn } from "@/shared/lib/utils";

interface EvaluationSummaryBannerProps {
  evaluations: EvaluationResponse[];
}

const VERDICT_STYLES: Record<string, string> = {
  hire: "bg-green-100 text-green-800 border-green-200",
  no_hire: "bg-red-100 text-red-800 border-red-200",
  needs_discussion: "bg-amber-100 text-amber-800 border-amber-200",
};

const CONFIDENCE_STYLES: Record<string, string> = {
  high: "bg-green-50 text-green-700",
  medium: "bg-amber-50 text-amber-700",
  low: "bg-red-50 text-red-700",
};

const STEP_STATUS_DOT: Record<string, string> = {
  completed: "bg-green-500",
  running: "bg-blue-500 animate-pulse",
  pending: "bg-amber-400",
  failed: "bg-red-500",
};

export function EvaluationSummaryBanner({ evaluations }: EvaluationSummaryBannerProps) {
  const stepMap = buildStepMap(evaluations);
  const recSummary = getRecommendationSummary(stepMap.recommendation?.result ?? null);
  const techSummary = getTechnicalSummary(stepMap.technical_eval?.result ?? null);

  const hasAnyEvaluation = evaluations.length > 0;

  if (!hasAnyEvaluation) {
    return (
      <div className="rounded-lg border border-dashed border-muted-foreground/25 bg-muted/30 px-6 py-4">
        <p className="text-sm text-muted-foreground">No evaluations yet</p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border bg-muted/20 px-6 py-4 space-y-3">
      <div className="flex items-center gap-6 flex-wrap">
        {/* Verdict + Confidence */}
        <div className="flex items-center gap-2">
          {recSummary.verdict ? (
            <Badge
              variant="outline"
              className={cn("text-sm font-medium capitalize", VERDICT_STYLES[recSummary.verdict])}
            >
              {recSummary.verdict.replace(/_/g, " ")}
            </Badge>
          ) : (
            <span className="text-sm text-muted-foreground">Verdict pending</span>
          )}
          {recSummary.confidence && (
            <Badge
              variant="outline"
              className={cn("text-xs capitalize", CONFIDENCE_STYLES[recSummary.confidence])}
            >
              {recSummary.confidence} confidence
            </Badge>
          )}
        </div>

        {/* Technical Score */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Technical:</span>
          {techSummary.score != null ? (
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold">{techSummary.metric}</span>
              <Progress
                value={(techSummary.score / techSummary.maxScore) * 100}
                className="h-2 w-16"
              />
            </div>
          ) : (
            <span className="text-sm text-muted-foreground">—</span>
          )}
        </div>

        {/* Pipeline Progress */}
        <div className="flex items-center gap-1.5 ml-auto">
          {STEP_ORDER.map((step) => {
            const ev = stepMap[step];
            const status = ev?.status ?? "not_started";
            return (
              <div key={step} className="group relative flex flex-col items-center">
                <div
                  className={cn(
                    "h-2.5 w-2.5 rounded-full",
                    STEP_STATUS_DOT[status] ?? "bg-muted-foreground/20"
                  )}
                />
                <div className="absolute -bottom-8 hidden group-hover:block z-10 whitespace-nowrap rounded bg-popover px-2 py-1 text-xs shadow-md border">
                  {getEvaluationStepLabel(step)}
                  {ev ? ` · ${formatEvaluationStatus(ev.status)}` : " · Not started"}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* One-liner */}
      {recSummary.oneLiner !== "—" && (
        <p className="text-sm text-muted-foreground leading-relaxed">{recSummary.oneLiner}</p>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Add export to index**

Add to `src/widgets/evaluations/index.ts`:
```ts
export { EvaluationSummaryBanner } from "./evaluation-summary-banner";
```

- [ ] **Step 3: Verify it compiles**

Run: `cd app/frontend && npx tsc --noEmit --pretty 2>&1 | head -20`
Expected: No errors

- [ ] **Step 4: Wire banner into candidate detail page**

In `src/routes/_authenticated/candidates/$candidateId.tsx`:
- Import `EvaluationSummaryBanner` from `@/widgets/evaluations`
- Import `useEvaluations` from `@/features/evaluations`
- After the page header div (containing the H1 name + Archive button) and before the `CandidateInfoCard`, add:

```tsx
{activeCandidatePositionId && (
  <EvaluationSummaryBanner
    evaluations={evaluationsData?.items ?? []}
  />
)}
```

This requires accessing evaluation data at the route level. The simplest approach: pass `evaluations` down from `EvaluationResults` via a callback, or call `useEvaluations` at the route level. Since `useEvaluations` must always be called (Rules of Hooks), guard with TanStack Query's `enabled` option to avoid an API call with invalid ID 0:

```tsx
const { data: evaluationsData } = useQuery({
  ...listEvaluationsApiEvaluationsCandidatePositionIdGetOptions({
    path: { candidate_position_id: activeCandidatePositionId ?? 0 },
  }),
  enabled: activeCandidatePositionId !== null,
});
```

Alternatively, use `useEvaluations` if it supports an `enabled` option. If not, add `enabled` support to `useEvaluations` in `src/features/evaluations/hooks/use-evaluations.ts`:
```ts
export function useEvaluations(candidatePositionId: number, options?: { enabled?: boolean }) {
  return useQuery({
    ...listEvaluationsApiEvaluationsCandidatePositionIdGetOptions({
      path: { candidate_position_id: candidatePositionId },
    }),
    enabled: options?.enabled ?? true,
  });
}
```

Then call at route level:
```tsx
const { data: evaluationsData } = useEvaluations(activeCandidatePositionId ?? 0, {
  enabled: activeCandidatePositionId !== null,
});
```

TanStack Query deduplicates identical queries, so the same call inside `EvaluationResults` won't double-fetch.

- [ ] **Step 5: Verify it compiles and renders**

Run: `cd app/frontend && npx tsc --noEmit --pretty 2>&1 | head -20`
Then visually verify at `http://localhost:5173/candidates/26` — the banner should appear between the header and the info card.

- [ ] **Step 6: Commit**

```bash
git add app/frontend/src/widgets/evaluations/evaluation-summary-banner.tsx \
  app/frontend/src/widgets/evaluations/index.ts \
  app/frontend/src/routes/_authenticated/candidates/\$candidateId.tsx
git commit -m "feat(frontend): add evaluation summary banner to candidate detail page"
```

---

## Chunk 2: Accordion Evaluation Steps

### Task 3: Refactor EvaluationStepCard to collapsible accordion

**Files:**
- Modify: `src/widgets/evaluations/evaluation-step-card.tsx`
- Modify: `src/widgets/evaluations/evaluation-results.tsx`

- [ ] **Step 1: Add accordion props and summary row to EvaluationStepCard**

Modify `EvaluationStepCardProps` to add:
```ts
interface EvaluationStepCardProps {
  evaluation: EvaluationResponse;
  candidatePositionId: number;
  resultContent?: ReactNode;
  disableRerun?: boolean;
  isOpen: boolean;
  onToggle: () => void;
}
```

Restructure the component to use `Collapsible` from `@/shared/ui/collapsible`:
- The card header becomes a `CollapsibleTrigger` containing: status badge, step label, key metric, one-liner, plus the Re-run/History buttons on the right
- The existing result content goes inside `CollapsibleContent`
- Import `getStepSummary` from `@/shared/lib/evaluation-summary`
- Add a chevron icon (ChevronDown from lucide-react) that rotates when open

The summary row in the header should display:
```tsx
const summary = getStepSummary(evaluation.step_type, evaluation.result);
// Render: [StatusBadge] Step Label · {summary.metric} · {summary.oneLiner} [Re-run] [History] [Chevron]
```

The completed timestamp should move inside `CollapsibleContent` (only visible when expanded).

- [ ] **Step 2: Add accordion state to EvaluationResults**

In `evaluation-results.tsx`:
- Add `useEffect` and `useState` to the React import: `import { useState, useEffect } from "react"`
- Add `useState<Set<string>>` for open panels:
  ```ts
  const [openPanels, setOpenPanels] = useState<Set<string>>(new Set());
  ```
- Create toggle handler:
  ```ts
  const togglePanel = (stepType: string) => {
    setOpenPanels((prev) => {
      const next = new Set(prev);
      if (next.has(stepType)) next.delete(stepType);
      else next.add(stepType);
      return next;
    });
  };
  ```
- Reset on `candidatePositionId` change:
  ```ts
  useEffect(() => {
    setOpenPanels(new Set());
  }, [candidatePositionId]);
  ```
- Pass `isOpen` and `onToggle` to each `EvaluationStepCard`:
  ```tsx
  <EvaluationStepCard
    key={ev.id}
    evaluation={ev}
    candidatePositionId={candidatePositionId}
    resultContent={<ResultRenderer stepType={ev.step_type} result={ev.result!} />}
    disableRerun={disableRerun}
    isOpen={openPanels.has(ev.step_type)}
    onToggle={() => togglePanel(ev.step_type)}
  />
  ```

- [ ] **Step 3: Verify it compiles and renders**

Run: `cd app/frontend && npx tsc --noEmit --pretty 2>&1 | head -20`
Then visually verify at `http://localhost:5173/candidates/26`:
- All 5 evaluation steps should render collapsed with summary rows
- Clicking a step should expand it showing the full results
- `HmDecisionGate` should still render between steps as before

- [ ] **Step 4: Commit**

```bash
git add app/frontend/src/widgets/evaluations/evaluation-step-card.tsx \
  app/frontend/src/widgets/evaluations/evaluation-results.tsx
git commit -m "feat(frontend): convert evaluation steps to collapsible accordion"
```

---

## Chunk 3: Evaluation Result Reordering + Polish

### Task 4: Reorder CV Analysis — Overall Fit above Skills Match

**Files:**
- Modify: `src/widgets/evaluations/cv-analysis-result.tsx`

- [ ] **Step 1: Reorder sections and polish**

In `cv-analysis-result.tsx`, move the "OVERALL FIT" section (currently last) to render first, before "SKILLS MATCH". The section order should be:
1. Overall Fit
2. Skills Match (with polish: tighter row padding, smaller badges, truncated notes)
3. Experience Relevance
4. Education
5. Signals & Red Flags

For Skills Match table polish:
- Reduce vertical padding on table rows: `py-2` instead of current `py-4`
- Make Present/Absent badges smaller: add `text-xs px-1.5 py-0` classes
- Truncate Notes column text to 80 chars with "Show more" toggle (reuse the `ExpandableCell` pattern from `technical-eval-result.tsx`, or create a simple inline version)

- [ ] **Step 2: Verify visually**

Navigate to `/candidates/26`, expand the CV Analysis accordion, confirm Overall Fit appears first and skills table looks tighter.

- [ ] **Step 3: Commit**

```bash
git add app/frontend/src/widgets/evaluations/cv-analysis-result.tsx
git commit -m "feat(frontend): reorder CV analysis — overall fit above skills, polish table"
```

---

### Task 5: Reorder Technical Evaluation — Strengths above Criteria Scores

**Files:**
- Modify: `src/widgets/evaluations/technical-eval-result.tsx`

- [ ] **Step 1: Reorder sections and polish**

Move "STRENGTHS" and "IMPROVEMENT AREAS" sections above the "CRITERIA SCORES" table. Current order: Weighted Score → Criteria Scores → Strengths → Improvements. New order: Weighted Score → Strengths → Improvements → Criteria Scores.

Polish:
- Add subtle green-tinted background (`bg-green-50/50`) to the Strengths container
- Add subtle amber-tinted background (`bg-amber-50/50`) to the Improvement Areas container
- In the Criteria Scores table, make Evidence and Reasoning columns collapsed by default using the existing `ExpandableCell` component
- Category grouping: add a subtle top border with different background (`bg-muted/30`) when `category_name` changes from the previous row

- [ ] **Step 2: Verify visually**

Navigate to `/candidates/26`, expand the Technical Evaluation accordion, confirm Strengths/Improvements appear before the scores table.

- [ ] **Step 3: Commit**

```bash
git add app/frontend/src/widgets/evaluations/technical-eval-result.tsx
git commit -m "feat(frontend): reorder technical eval — strengths above scores, polish table"
```

---

### Task 6: Reorder Screening Evaluation

**Files:**
- Modify: `src/widgets/evaluations/screening-eval-result.tsx`

- [ ] **Step 1: Reorder sections**

Move "KEY TOPICS" and "STRENGTHS" above "CONCERNS", "COMMUNICATION QUALITY", and "MOTIVATION & CULTURE FIT". Current order: Key Topics → Strengths → Concerns → Communication → Motivation. This order is already correct — no reordering needed. But verify and add a subtle green-tinted background to Strengths and amber-tinted background to Concerns for visual consistency with the Technical Evaluation.

- [ ] **Step 2: Verify visually and commit**

```bash
git add app/frontend/src/widgets/evaluations/screening-eval-result.tsx
git commit -m "feat(frontend): polish screening eval — tinted strengths/concerns sections"
```

---

## Chunk 4: Shared Document Content Extraction

### Task 7: Extract document content fetching into shared hook

**Files:**
- Create: `src/features/documents/hooks/use-document-content.ts`
- Modify: `src/features/documents/index.ts` (add export)

- [ ] **Step 1: Create the shared hook**

Extract the content fetching + state machine from `document-viewer.tsx` into a reusable hook:

```ts
// src/features/documents/hooks/use-document-content.ts

import { useEffect, useState } from "react";
import mammoth from "mammoth";
import DOMPurify from "dompurify";

export type ContentState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; content: string }
  | { status: "error"; error: string };

export function useDocumentContent(
  viewUrl: string | null | undefined,
  contentType: string | null | undefined,
  enabled: boolean
): ContentState {
  const [state, setState] = useState<ContentState>({ status: "idle" });

  useEffect(() => {
    if (!enabled || !viewUrl || !contentType) {
      setState({ status: "idle" });
      return;
    }

    if (contentType === "application/pdf") {
      setState({ status: "success", content: viewUrl });
      return;
    }

    setState({ status: "loading" });

    const controller = new AbortController();

    (async () => {
      try {
        const response = await fetch(viewUrl, { signal: controller.signal });
        if (!response.ok) throw new Error(`Failed to fetch: ${response.statusText}`);

        if (contentType === "application/vnd.openxmlformats-officedocument.wordprocessingml.document") {
          const arrayBuffer = await response.arrayBuffer();
          const result = await mammoth.convertToHtml({ arrayBuffer });
          // Preserve the same DOMPurify options as the original DocumentViewer
          // Check document-viewer.tsx for any ALLOWED_TAGS/ALLOWED_ATTR config and replicate here
          setState({ status: "success", content: DOMPurify.sanitize(result.value) });
        } else {
          const text = await response.text();
          setState({ status: "success", content: text });
        }
      } catch (err) {
        if (!controller.signal.aborted) {
          setState({ status: "error", error: err instanceof Error ? err.message : "Unknown error" });
        }
      }
    })();

    return () => controller.abort();
  }, [viewUrl, contentType, enabled]);

  return state;
}
```

- [ ] **Step 2: Add export to features/documents/index.ts**

```ts
export { useDocumentContent } from "./hooks/use-document-content";
export type { ContentState } from "./hooks/use-document-content";
```

- [ ] **Step 3: Commit**

```bash
git add app/frontend/src/features/documents/hooks/use-document-content.ts \
  app/frontend/src/features/documents/index.ts
git commit -m "feat(frontend): extract document content fetching into shared hook"
```

---

### Task 8: Create DocumentContentRenderer component

**Files:**
- Create: `src/widgets/documents/document-content-renderer.tsx`
- Modify: `src/widgets/documents/index.ts` (add export)

- [ ] **Step 1: Create the renderer component**

```tsx
// src/widgets/documents/document-content-renderer.tsx

import ReactMarkdown from "react-markdown";
import type { ContentState } from "@/features/documents";
import { Skeleton } from "@/shared/ui/skeleton";
import { AlertCircle } from "lucide-react";

interface DocumentContentRendererProps {
  contentState: ContentState;
  contentType: string;
  className?: string;
}

export function DocumentContentRenderer({
  contentState,
  contentType,
  className,
}: DocumentContentRendererProps) {
  if (contentState.status === "idle" || contentState.status === "loading") {
    return (
      <div className={className}>
        <Skeleton className="h-4 w-full mb-2" />
        <Skeleton className="h-4 w-3/4 mb-2" />
        <Skeleton className="h-4 w-5/6" />
      </div>
    );
  }

  if (contentState.status === "error") {
    return (
      <div className={`flex items-center gap-2 text-destructive ${className ?? ""}`}>
        <AlertCircle className="h-4 w-4" />
        <span className="text-sm">{contentState.error}</span>
      </div>
    );
  }

  const { content } = contentState;

  if (contentType === "application/pdf") {
    return <iframe src={content} className={`w-full h-full ${className ?? ""}`} title="PDF viewer" />;
  }

  if (contentType === "application/vnd.openxmlformats-officedocument.wordprocessingml.document") {
    return (
      <div
        className={`prose prose-sm max-w-none dark:prose-invert ${className ?? ""}`}
        dangerouslySetInnerHTML={{ __html: content }}
      />
    );
  }

  if (contentType === "text/markdown") {
    return (
      <div className={`prose prose-sm max-w-none dark:prose-invert ${className ?? ""}`}>
        <ReactMarkdown>{content}</ReactMarkdown>
      </div>
    );
  }

  // text/plain and fallback
  return (
    <pre className={`text-sm whitespace-pre-wrap font-mono ${className ?? ""}`}>
      {content}
    </pre>
  );
}
```

- [ ] **Step 2: Add export to widgets/documents/index.ts**

```ts
export { DocumentContentRenderer } from "./document-content-renderer";
```

- [ ] **Step 3: Refactor DocumentViewer to use shared hook + renderer**

In `src/widgets/documents/document-viewer.tsx`:
- Remove the internal `ContentState` type and `useState<ContentState>` + `useEffect` that fetches content
- Replace with:
  ```ts
  import { useDocumentContent } from "@/features/documents";
  import { DocumentContentRenderer } from "./document-content-renderer";
  ```
- Call the hook:
  ```ts
  const contentState = useDocumentContent(
    document?.view_url,
    document?.content_type,
    open && !!document
  );
  ```
- Replace `renderContent()` function body with `DocumentContentRenderer`. This must stay inside the existing `if (!document) return ...` guard so that `document` is narrowed to non-null:
  ```tsx
  <DocumentContentRenderer
    contentState={contentState}
    contentType={document.content_type}
  />
  ```

- [ ] **Step 4: Verify DocumentViewer still works**

Navigate to `/candidates/26`, click a CV document — it should still open in a dialog and render correctly.

- [ ] **Step 5: Commit**

```bash
git add app/frontend/src/widgets/documents/document-content-renderer.tsx \
  app/frontend/src/widgets/documents/document-viewer.tsx \
  app/frontend/src/widgets/documents/index.ts
git commit -m "feat(frontend): create shared DocumentContentRenderer, refactor DocumentViewer"
```

---

## Chunk 5: Inline Tabbed Transcripts

### Task 9: Create InlineTranscriptViewer component

**Files:**
- Create: `src/widgets/documents/inline-transcript-viewer.tsx`
- Modify: `src/widgets/documents/index.ts` (add export)

- [ ] **Step 1: Create the inline transcript viewer**

```tsx
// src/widgets/documents/inline-transcript-viewer.tsx

import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/shared/ui/tabs";
import { Skeleton } from "@/shared/ui/skeleton";
import { useDocument, useDocumentContent } from "@/features/documents";
import { DocumentContentRenderer } from "./document-content-renderer";
import { formatDate } from "@/shared/lib/format";
import type { DocumentResponse } from "@/shared/api";
import { CalendarIcon, UserIcon } from "lucide-react";

interface InlineTranscriptViewerProps {
  transcripts: DocumentResponse[];
}

function buildTabLabel(doc: DocumentResponse, allTranscripts: DocumentResponse[]): string {
  const stage = doc.interview_stage ?? "Interview";
  const sameStage = allTranscripts.filter((t) => t.interview_stage === doc.interview_stage);
  if (sameStage.length <= 1) return stage;
  if (doc.interview_date) return `${stage} – ${formatDate(doc.interview_date)}`;
  const idx = sameStage.findIndex((t) => t.id === doc.id);
  return `${stage} (${idx + 1})`;
}

function TranscriptTab({ documentId }: { documentId: number }) {
  const { data: document, isLoading: metaLoading } = useDocument(documentId, { enabled: true });
  const contentState = useDocumentContent(
    document?.view_url,
    document?.content_type,
    !!document
  );

  if (metaLoading) {
    return (
      <div className="space-y-2 p-4">
        <Skeleton className="h-4 w-48" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-3/4" />
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Metadata header */}
      {document && (
        <div className="flex items-center gap-4 text-xs text-muted-foreground px-1">
          {document.interviewer_name && (
            <span className="flex items-center gap-1">
              <UserIcon className="h-3 w-3" />
              {document.interviewer_name}
            </span>
          )}
          {document.interview_date && (
            <span className="flex items-center gap-1">
              <CalendarIcon className="h-3 w-3" />
              {formatDate(document.interview_date)}
            </span>
          )}
        </div>
      )}
      {document?.notes && (
        <p className="text-xs text-muted-foreground italic border-l-2 border-muted pl-2">{document.notes}</p>
      )}
      {/* Content */}
      <div className="max-h-[500px] overflow-y-auto rounded-md border bg-muted/10 p-4">
        <DocumentContentRenderer
          contentState={contentState}
          contentType={document?.content_type ?? "text/plain"}
        />
      </div>
    </div>
  );
}

export function InlineTranscriptViewer({ transcripts }: InlineTranscriptViewerProps) {
  const [activeTab, setActiveTab] = useState(String(transcripts[0]?.id ?? ""));

  if (transcripts.length === 0) return null;

  if (transcripts.length === 1) {
    return <TranscriptTab documentId={transcripts[0].id} />;
  }

  return (
    <Tabs value={activeTab} onValueChange={setActiveTab}>
      <TabsList>
        {transcripts.map((doc) => (
          <TabsTrigger key={doc.id} value={String(doc.id)}>
            {buildTabLabel(doc, transcripts)}
          </TabsTrigger>
        ))}
      </TabsList>
      {transcripts.map((doc) => (
        <TabsContent key={doc.id} value={String(doc.id)}>
          {activeTab === String(doc.id) && <TranscriptTab documentId={doc.id} />}
        </TabsContent>
      ))}
    </Tabs>
  );
}
```

Note: The `TabsContent` only renders `TranscriptTab` when active — this implements lazy-loading per tab since `useDocument` only fires when the component mounts.

- [ ] **Step 2: Add export**

Add to `src/widgets/documents/index.ts`:
```ts
export { InlineTranscriptViewer } from "./inline-transcript-viewer";
```

- [ ] **Step 3: Commit**

```bash
git add app/frontend/src/widgets/documents/inline-transcript-viewer.tsx \
  app/frontend/src/widgets/documents/index.ts
git commit -m "feat(frontend): create inline tabbed transcript viewer component"
```

---

### Task 10: Integrate inline transcripts into candidate detail page

**Files:**
- Modify: `src/widgets/documents/document-list.tsx`
- Modify: `src/routes/_authenticated/candidates/$candidateId.tsx`

- [ ] **Step 1: Add inline transcript viewer below document table**

In `document-list.tsx`, after the document table rendering, add a section that renders `InlineTranscriptViewer` for transcript documents. Filter the documents to only transcripts:

```tsx
import { InlineTranscriptViewer } from "./inline-transcript-viewer";

// Inside the component, after the table:
const transcriptDocs = documents?.filter((d) => d.type === "transcript") ?? [];

// After the table JSX:
{transcriptDocs.length > 0 && (
  <div className="mt-6 space-y-2">
    <h4 className="text-sm font-medium text-muted-foreground">Transcript Viewer</h4>
    <InlineTranscriptViewer transcripts={transcriptDocs} />
  </div>
)}
```

- [ ] **Step 2: Update document click behavior for transcripts**

In `$candidateId.tsx`, modify `onDocumentClick` to not open the dialog for transcripts. Instead, scroll to the inline viewer. The simplest approach: in `DocumentList`, when a transcript row is clicked, instead of calling `onDocumentClick`, scroll to the inline viewer and activate the corresponding tab.

Add an `onTranscriptClick` prop to `DocumentList` alongside `onDocumentClick`, or have `DocumentList` handle transcripts internally by scrolling to the `InlineTranscriptViewer` section.

Simplest approach — add a ref to the transcript viewer section and scroll to it:
```tsx
const transcriptViewerRef = useRef<HTMLDivElement>(null);

// In the transcript viewer section:
<div ref={transcriptViewerRef} className="mt-6 space-y-2">
```

For transcript rows in the table, replace the `onDocumentClick` call with scroll + tab activation.

- [ ] **Step 3: Verify visually**

Navigate to `/candidates/26`:
- Documents card should show the table as before, plus a new "Transcript Viewer" section below with tabs
- Clicking a transcript row should scroll to the viewer and show that transcript
- Clicking a CV row should still open the dialog

- [ ] **Step 4: Commit**

```bash
git add app/frontend/src/widgets/documents/document-list.tsx \
  app/frontend/src/routes/_authenticated/candidates/\$candidateId.tsx
git commit -m "feat(frontend): integrate inline transcript viewer into documents card"
```

---

## Chunk 6: Final Wiring + Cleanup

### Task 11: Final type-check, visual review, and cleanup

**Files:**
- All modified files

- [ ] **Step 1: Full type check**

Run: `cd app/frontend && npx tsc --noEmit --pretty`
Expected: No errors

- [ ] **Step 2: Lint check**

Run: `cd app/frontend && bun run lint`
Expected: No errors in modified files

- [ ] **Step 3: Build check**

Run: `cd app/frontend && bun run build`
Expected: Successful build

- [ ] **Step 4: Visual review**

Navigate to `http://localhost:5173/candidates/26` and verify:
1. Summary banner appears below header with correct verdict, score, pipeline dots
2. All evaluation steps are collapsed by default with summary rows
3. Clicking expands/collapses correctly; multiple can be open
4. HM Decision Gate renders between screening → technical and recommendation → feedback steps
5. CV Analysis expanded: Overall Fit appears first, skills table has tighter rows
6. Technical Evaluation expanded: Strengths/Improvements above criteria scores
7. Transcript viewer appears inline in Documents card with tabs
8. CV click still opens dialog
9. Accordion state resets when switching position tabs (if candidate has multiple)

- [ ] **Step 5: Final commit if any cleanup needed**

```bash
git add -u
git commit -m "chore(frontend): cleanup and polish candidate detail UI refinement"
```
