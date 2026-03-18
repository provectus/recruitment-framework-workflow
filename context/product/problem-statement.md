# Problem Statement: Recruitment Candidate Profiling

- **Version:** 1.1
- **Date:** 2026-03-18
- **Status:** Conditionally Approved (pilot)

---

## The Problem

Hiring Managers spend significant time reviewing raw candidate materials (CVs, Lever profiles, screening call recordings, HR feedback) to decide whether a candidate is worth a technical interview. Despite this effort, mismatched candidates still reach the technical interview stage — costing HM time and company money.

HR already filters obvious rejects (fake identities, clearly unqualified). The candidates reaching the HM are **borderline or misleadingly decent** — they pass a recruiter's filter but don't survive domain-expert scrutiny. The signal HR misses is technical: shallow depth disguised by good communication, skills that don't actually match the position's requirements, or experience that looks relevant but isn't.

### Pain Points

1. **HM review overhead** — HM manually reviews CV, Lever profile, screening recording, and HR notes for every candidate. This takes ~30 min per candidate even for rejects.
2. **Wasted technical interviews** — Candidates who pass screening but fail technical interviews represent the highest cost: HM time + interviewer time + scheduling overhead.
3. **Implicit criteria** — What "good" looks like lives in the HM's head and evolves with industry trends (e.g., AI workflow proficiency is now critical but wasn't 6 months ago). Generic rubrics can't keep up.
4. **No feedback loop** — When a candidate is rejected at technical stage, that signal doesn't flow back to improve screening quality.

### Open Risk

The core assumption is that the bottleneck is information format (raw → structured). If candidates fail technical for reasons invisible in documents — thinking depth, communication under pressure, real-time problem solving — better pre-reads won't reduce wasted technicals. The pilot must validate this with live candidates.

### What We're NOT Solving

- Automating the hiring decision — HM always makes the call
- Replacing HR screening — HR still conducts calls and filters obvious mismatches
- Full pipeline automation — the goal is structured insight, not end-to-end automation

---

## The Solution

Two-stage AI candidate profiling that compresses raw materials into structured, HM-oriented summaries at two gates. A third feedback stage is designed but parked until candidate volume justifies it.

### Stage 1: CV Brief Profile (Pre-Screening)

**Input:** CV + position requirements (from Lauter)
**Output:** Structured profile mapping candidate against position requirements
**Purpose:** Give HR targeted questions for the screening call and give HM an early signal

- Map stated skills/experience against position must-haves and nice-to-haves
- Flag gaps, inconsistencies, and red flags
- Suggest specific areas to probe during screening call
- Show specific CV excerpts alongside assessments — claims must be verifiable on the spot
- Brief enough to read in 2 minutes

### Stage 2: Post-Screening Enriched Profile (Pre-Technical)

**Input:** CV + screening call transcript + HR notes + position requirements
**Output:** Enriched profile incorporating screening findings
**Purpose:** Give HM a compressed view to decide on technical interview, and focus areas if they proceed

- Update profile with screening findings (did the candidate address CV gaps?)
- Highlight remaining unknowns and risk areas
- Recommend specific topics to dig into during technical interview
- Target: replace 30-min raw material review with structured read (early on, HMs will read profile AND raw materials to calibrate trust — that's expected)

### Stage 3: Process Feedback Loop (Post-Outcome) — PARKED

> Parked until a single position processes 5+ candidates and there's enough signal for the loop to learn. Most positions hire 1-2 people — the loop barely warms up before the role is filled. Most valuable at high-volume junior hiring, least valuable at senior/specialized roles where mismatches hurt most.

**Trigger:** After any outcome — rejection at HM review, rejection at technical, hire, or probation result
**Input:** All prior AI profiles + interview transcripts + outcome
**Output:** Process insights that feed forward into the next candidate for the same position

**Post-screening analysis (fed back to HR):**
- Did the screening call probe the areas the CV profile flagged?
- Were there gaps the screening missed that surfaced at technical?
- Suggested adjustments to screening approach for the next candidate

**Post-technical analysis (fed back to HM/interviewer):**
- Did the technical interview cover the enriched profile's recommended focus areas?
- Did the outcome validate or contradict the AI's assessment?
- What should the next interviewer prioritize differently?

### Key Design Principles

- **Profile, don't judge** — AI maps candidate against requirements and highlights signals. It does not make go/no-go recommendations.
- **Speak the HM's language** — Output reflects domain-specific criteria, not generic HR-speak.
- **Criteria are living** — Position requirements in Lauter are the anchor, maintained by the HM. HMs can use AI tools to synthesize quality requirements from their experience.
- **Position requirements are load-bearing** — The system's output quality is bounded by how well requirements are defined. Mitigated by HM incentive alignment: garbage requirements → garbage candidates on their calendar.
- **Process learns** — Every outcome refines screening questions and interview focus for the next candidate (when Stage 3 is activated).
- **Measurable value** — Track HM time-to-decision and technical interview pass rate.

---

## Pilot Plan

### Scope

- **Stages:** 1 (CV Brief Profile) + 2 (Enriched Profile) together
- **Positions:** 2-3 active positions with motivated HMs
- **Volume:** ~10-15 candidates through the pipeline

### Prompt Calibration (Pre-Pilot)

Use 10-20 historical candidates with known outcomes to tune output structure, gap flag placement, and language usefulness. This is **calibration, not validation** — hindsight bias makes every retrospective profile look prescient.

### Measurement

No analytics dashboards at pilot scale. Two lightweight signals:
1. **Structured HM debrief** every 5 candidates: Did you read the profile first? Did it change or speed up your decision? What was useless?
2. **Two database fields:** `profile_viewed_at` and `decision_made_at` — delta measures decision acceleration

### Kill Criterion

If after 10-15 live candidates HMs are ignoring profiles or still reading raw CVs cover to cover, pull the plug and redirect effort. Without a defined exit, internal tools live forever on "we just need to tune it more."

---

## Current State

- Position requirements already defined in Lauter (duplicated from Lever until integration is validated)
- CV analysis and screening summary capabilities exist in the pipeline (Step Functions + Lambda + Bedrock)
- Lever integration is deferred — Lauter operates standalone until value is proven
- No historical rejection rate data available from Lever
- Cost-benefit math (candidates/month, technical rejection rate, loaded cost of wasted interviews, build/maintain cost) needed before scaling beyond pilot

---

## Parked Items

| Item | Revisit When |
|------|-------------|
| Stage 3: Feedback Loop | Single position processes 5+ candidates |
| Analytics infrastructure | Pilot scales beyond 2-3 positions |
| Cost-benefit analysis | Before scaling beyond pilot |
| Lever integration | Lauter value proven in pilot |
