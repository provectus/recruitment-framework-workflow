# Problem Statement Review: Engineering Leadership Critique

- **Date:** 2026-03-18
- **Reviewer:** Head of Engineering (simulated)
- **Status:** Conditionally Approved

---

## Verdict

Stage 1 + Stage 2 greenlit as a live pilot on 2-3 positions. Stage 3 (feedback loop) parked until candidate volume justifies it. Historical data used for prompt calibration only, not validation.


## What Holds Up

- **Real pain point.** 30 min/candidate HM review for rejects is measurable waste that scales with open positions.
- **Feedback loop (Stage 3) is the differentiator.** Most AI-for-hiring stops at summarization. Per-candidate process refinement is where compounding value lives — but only at sufficient volume.
- **Deliberately narrow scope.** "Profile, don't judge" avoids the legal and ethical minefield of automated hiring decisions. HM stays in the decision seat.
- **Profile as gap analysis, not summary.** Value holds if profiles cross-reference candidate claims against position requirements and flag mismatches — not just reformat the CV.

## Key Critiques

### Core assumption needs live validation
The pitch assumes the bottleneck is information format (raw → structured). If candidates fail technical for reasons invisible in documents (thinking depth, communication under pressure), better pre-reads don't reduce wasted technicals. Must validate with live candidates, not retrospectives.

### Position requirements quality is load-bearing
The entire system's output quality is bounded by how well requirements are defined. Mitigated by HM incentive alignment: garbage requirements → garbage candidates on their calendar. HMs can use AI tools to synthesize quality requirements from their experience.

### Feedback loop has cold start and data sparsity
- Most positions hire 1-2 people — loop barely warms up before the role is filled.
- Senior/specialized roles (where mismatches hurt most) have the fewest candidates to learn from.
- Most valuable where least needed (high-volume junior hiring).
- **Decision:** Park Stage 3 until volume justifies it.

### Retrospective validation proves the wrong thing
Running historical candidates with known outcomes through the pipeline confirms the AI can generate plausible summaries — hindsight bias makes every profile look prescient. Historical data is valid for **prompt calibration** (tuning output structure, gap flag placement, language usefulness) but not for proving the system changes decisions.

### No cost-benefit math in the doc
Missing numbers: candidates/month reaching HM review, current technical rejection rate, loaded cost of wasted technical interviews, build/maintain cost. Needed before scaling beyond pilot.

### "2-min read" claim is aspirational
Early on, HMs will read profile AND raw materials to calibrate trust. Adoption isn't instant. The trust gap collapses faster if profiles show specific CV excerpts alongside assessments — making claims verifiable on the spot.


## Approved Approach

### Pilot scope
- **Stages:** 1 (CV Brief Profile) + 2 (Enriched Profile) together
- **Positions:** 2-3 active positions with motivated HMs
- **Volume:** ~10-15 candidates through the pipeline
- **Prompt calibration:** Use historical candidate data to tune output structure and language before going live

### Measurement (keep it simple)
No analytics dashboards at pilot scale. Two lightweight signals:
1. **Structured HM debrief** every 5 candidates: Did you read the profile first? Did it change or speed up your decision? What was useless?
2. **Two database fields:** `profile_viewed_at` and `decision_made_at` — delta measures decision acceleration. Already have the backend for this.

### Kill criterion
If after 10-15 live candidates HMs are ignoring profiles or still reading raw CVs cover to cover, pull the plug and redirect effort. Without a defined exit, internal tools live forever on "we just need to tune it more."

### What stays parked
- **Stage 3 (feedback loop):** Revisit when a single position processes 5+ candidates and there's enough signal for the loop to learn.
- **Analytics infrastructure:** Revisit when pilot scales beyond 2-3 positions.
