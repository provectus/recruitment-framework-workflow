# Functional Specification: Recruitment Interview Evaluation Pipeline

- **Roadmap Item:** Phase 2 — Evaluation Pipeline (Screening Summary, HM Review & Decision Gate, Technical Evaluation, Recommendation Generation)
- **Status:** Completed
- **Author:** Nail / Claude

---

## 1. Overview and Rationale (The "Why")

Today, hiring managers and recruiters manually evaluate candidates by copying interview transcripts into Claude, cross-referencing with job requirements, and applying evaluation frameworks by hand. This is repetitive, inconsistent, and slow — each evaluation takes 30-60 minutes of manual work, and the quality varies based on who does it and how much time they have.

The evaluation pipeline automates this end-to-end. When a document (CV or transcript) is uploaded for a candidate, the system automatically analyzes it using Claude AI against the position's requirements and rubric. Results appear inline on the candidate's page — structured summaries, numeric scores, and a final hire/no-hire recommendation with transparent reasoning.

**Success looks like:**
- Zero manual copy-paste between tools — upload triggers evaluation automatically
- Consistent scoring across all candidates for a position using the same rubric
- HMs receive structured, actionable evaluation results within minutes of transcript upload
- Full audit trail of every evaluation for compliance and review

---

## 2. Functional Requirements (The "What")

### 2.1 Pipeline Trigger & Lifecycle

- When a CV is uploaded and linked to a candidate+position, the **cv-analysis** step triggers automatically
- When a screening transcript is uploaded for a candidate+position, the **screening-eval** step triggers automatically
- When a technical transcript is uploaded for a candidate+position, the **technical-eval** step triggers automatically, followed by **recommendation**
- The **recommendation** step runs after technical-eval completes (or after any upstream step is re-run) and aggregates results from all prior steps (cv-analysis + screening-eval + technical-eval)
- The **feedback-gen** step triggers when an HM marks a candidate as "rejected" at any decision gate
  - **Acceptance Criteria:**
    - [x] Uploading a CV for a candidate with a linked position auto-triggers cv-analysis within 10 seconds
    - [x] Uploading a screening transcript auto-triggers screening-eval within 10 seconds
    - [x] Uploading a technical transcript auto-triggers technical-eval, which upon completion triggers recommendation
    - [x] Rejecting a candidate triggers feedback-gen
    - [x] No evaluation runs if the candidate is not linked to a position
    - [x] No technical-eval runs if the position has no rubric assigned

### 2.2 CV Analysis

- Input: uploaded CV (from S3) + position requirements (title, description, required skills)
- Output: structured analysis with:
  - **Skills match:** which required skills are present/absent in the CV
  - **Experience relevance:** how relevant the candidate's experience is to the role
  - **Education & certifications:** relevant qualifications
  - **Signals & red flags:** notable positives (e.g., domain expertise) and concerns (e.g., frequent job changes, gaps)
  - **Overall fit assessment:** brief narrative summary of CV-to-role alignment
  - **Acceptance Criteria:**
    - [x] Analysis covers all four sections: skills match, experience relevance, education, signals/red flags
    - [x] Each required skill from the position is individually addressed as present or absent
    - [x] Analysis is stored in the database linked to the candidate, position, and source document
    - [x] If the CV is unreadable or empty, the step fails with a clear error message: "CV could not be parsed"

### 2.3 Screening Evaluation

- Input: screening transcript text + position requirements
- Output: structured summary with labeled sections:
  - **Key topics discussed:** bullet list of main subjects covered
  - **Candidate strengths:** positive signals from the conversation
  - **Concerns or risks:** any yellow/red flags identified
  - **Communication quality:** assessment of how clearly the candidate communicated
  - **Motivation & culture fit:** signals about why the candidate wants the role and cultural alignment
  - **Acceptance Criteria:**
    - [x] Summary contains all five labeled sections
    - [x] Each section contains at least one bullet point (or "No significant signals identified" if none)
    - [x] Summary is stored linked to the candidate, position, and source transcript
    - [x] If the transcript is too short (< 100 words), the step fails with: "Transcript too short for meaningful analysis"

### 2.4 Technical Evaluation

- Input: technical interview transcript + position rubric (from PositionRubric with versioned structure)
- Output: rubric-based scored evaluation:
  - **Per-criterion scores:** each rubric criterion scored 1-5 with:
    - Numeric score (1-5)
    - Supporting evidence: specific quotes or examples from the transcript
    - Reasoning: why this score was assigned
  - **Weighted total score:** calculated from criterion scores and rubric weights
  - **Strengths summary:** top 2-3 strongest areas
  - **Improvement areas:** top 2-3 weakest areas
  - **Acceptance Criteria:**
    - [x] Every criterion in the position rubric receives a score between 1 and 5
    - [x] Each scored criterion includes at least one supporting quote from the transcript
    - [x] Weighted total score is correctly calculated from individual scores and rubric weights
    - [x] Evaluation references the specific rubric version used (for audit)
    - [x] If the position has no rubric, the step does not run and shows: "No rubric assigned to this position"

### 2.5 Recommendation

- Input: aggregated results from cv-analysis + screening-eval + technical-eval (whichever are available)
- Output:
  - **Recommendation:** Hire / No Hire / Needs Discussion
  - **Confidence level:** High / Medium / Low
  - **Reasoning:** narrative explaining the recommendation, referencing evidence from prior steps
  - **Missing data disclaimer:** if any upstream step failed or was not run, the recommendation explicitly notes which inputs were unavailable and how that affects confidence
  - **Acceptance Criteria:**
    - [x] Recommendation is one of: Hire, No Hire, Needs Discussion
    - [x] Confidence level is one of: High, Medium, Low
    - [x] If any upstream evaluation is missing (step failed or not run), confidence is capped at "Low" and the missing data is explicitly stated
    - [x] Reasoning references specific scores and findings from prior steps
    - [x] Recommendation is stored linked to the candidate and position

### 2.6 Feedback Generation (on rejection)

- Input: all available evaluation results + rejection stage (screening or technical)
- Output:
  - **Draft feedback text:** professional, constructive candidate-facing feedback
  - **Tone:** respectful, encouraging, non-discriminatory
  - **Content:** acknowledges candidate strengths, provides actionable areas for improvement, does not reveal internal scores or rubric details
  - **Acceptance Criteria:**
    - [x] Feedback draft is generated when HM clicks "Reject" on a candidate
    - [x] Feedback does not expose numeric scores, rubric criteria names, or internal evaluation details
    - [x] Feedback mentions at least one candidate strength
    - [x] Feedback is stored as a draft (not sent automatically) for HM review
    - [x] HM can edit the feedback draft before finalizing

### 2.7 Results Display (Candidate Page)

- Evaluation results appear as sections on the candidate detail page, within the context of a specific position
- Each evaluation section shows:
  - Step name (e.g., "CV Analysis", "Technical Evaluation")
  - Status badge: Pending → Running → Complete → Failed
  - Timestamp of completion
  - Results content (structured per step, as defined above)
- When an evaluation is running, the status badge shows "Running" and a toast notification appears when it completes
- Failed steps show the failure reason inline with an option to retry
  - **Acceptance Criteria:**
    - [x] Each evaluation step has a visible status badge on the candidate page
    - [x] Status transitions: Pending → Running → Complete or Failed
    - [x] User receives a toast notification when any evaluation step completes or fails
    - [x] Completed evaluations display their full structured results inline
    - [x] Failed evaluations show the failure reason and a "Retry" button
    - [x] Results are scoped to the candidate+position combination (a candidate evaluated for two positions shows separate results)

### 2.8 Re-run & Cascading

- Users can re-run any individual evaluation step via a "Re-run" button on completed or failed evaluations
- Re-running a step also triggers all downstream dependent steps:
  - Re-run cv-analysis → re-triggers recommendation (if technical-eval exists)
  - Re-run screening-eval → re-triggers recommendation (if technical-eval exists)
  - Re-run technical-eval → re-triggers recommendation
- Previous results are preserved in history for audit; the latest result is displayed
  - **Acceptance Criteria:**
    - [x] Each completed or failed evaluation step shows a "Re-run" button
    - [x] Re-running technical-eval automatically re-runs recommendation after it completes
    - [x] Previous evaluation results are preserved and accessible (not overwritten)
    - [x] The candidate page always displays the most recent evaluation result

### 2.9 Error Handling (Fault-Tolerant Pipeline)

- If a step fails (Bedrock timeout, malformed input, etc.), the failure is recorded and the pipeline **continues to subsequent steps**
- The failed step's error reason is stored and included in the final recommendation report
- The recommendation step accounts for missing data — clearly stating which inputs were unavailable
  - **Acceptance Criteria:**
    - [x] A failed cv-analysis does not block screening-eval or technical-eval from running
    - [x] A failed screening-eval does not block technical-eval from running
    - [x] The recommendation step runs even if upstream steps failed, noting missing inputs
    - [x] Each failure records: step name, error type, error message, timestamp
    - [x] The end-to-end report clearly indicates which steps succeeded and which failed

### 2.10 HM Decision Gate

- After evaluation results are available, the HM can make a decision on the candidate:
  - **After screening:** "Proceed to Technical" or "Reject"
  - **After recommendation:** "Hire" or "Reject"
- The decision is recorded with optional HM notes
- "Reject" at any stage triggers feedback-gen
  - **Acceptance Criteria:**
    - [x] HM sees "Proceed to Technical" and "Reject" buttons after screening-eval completes
    - [x] HM sees "Hire" and "Reject" buttons after recommendation completes
    - [x] Decision is recorded with timestamp, HM identity, and optional notes
    - [x] Rejecting triggers the feedback-gen step automatically

---

## 3. Scope and Boundaries

### In-Scope
- Auto-triggering evaluation steps on document upload
- CV analysis against position requirements
- Screening transcript structured summary
- Technical transcript rubric-based evaluation with numeric (1-5) scoring
- Aggregated recommendation with confidence and reasoning
- Rejection feedback draft generation
- Inline evaluation results on candidate page with status badges and notifications
- Re-running individual steps with cascading to dependents
- Fault-tolerant pipeline (failed steps don't block others)
- HM decision gates (proceed/reject) at screening and recommendation stages
- Evaluation history (previous results preserved for audit)

### Out-of-Scope
- **Interview Library** (separate roadmap item — Phase 1)
- **Barley Integration / S3 Transcript Sync** (separate roadmap item — Phase 1)
- **Candidate Feedback Templates** (Phase 3 — this spec covers draft generation only, not template management)
- **Lever Integration** (Future phase — read/write candidate data, feedback form drafting)
- **Real-time streaming of AI output** (results appear after step completes, not token-by-token)
- **Multi-position evaluation comparison** (comparing a candidate's evaluations across different positions)
- **Automated email sending** of feedback to candidates
- **Editing AI evaluation results** (HM is view-only on AI output; they make decisions, not edits)
