# Pilot Plan: Candidate Profiling

- **Version:** 1.0
- **Date:** 2026-03-18
- **Status:** Draft — pending Head of IT alignment on Lever integration feasibility
- **Scope:** 2-3 positions, ~10-15 candidates
- **Kill criterion:** If after 10-15 live candidates HMs ignore profiles or still read raw CVs cover to cover → pull the plug

---

## Integration Landscape

```
Lever (ATS)                    Barley (Recordings)
  │ webhook: stage transition    │ webhook: recording ready
  │ API: read CV, write notes    │ API: query transcripts
  ▼                              ▼
              Lauter (Orchestration + AI)
              │  Pipeline: Step Functions + Lambda + Bedrock
              │  UI: HM-facing candidate profiles
              │  DB: measurement tracking
```

**HR stays in Lever. HM uses Lauter. Nobody opens a new tool they don't already use.**

---

## Pilot Data Flow

1. **Lever webhook** → candidate hits trigger stage (e.g., "New Applicant") on a pilot position
2. Lauter pulls **CV + candidate data** from Lever API
3. AI generates **CV Brief Profile** (gap analysis vs position requirements + screening questions)
4. Lauter pushes CV Brief Profile as a **note back to Lever** (HR sees it before screening)
5. HR conducts screening call (no workflow change)
6. **Barley webhook** → screening recording ready
7. Lauter queries Barley API, matches candidate by **email** (fallback: name + position + date window), pulls transcript
8. AI generates **Enriched Profile** (cross-references screening against CV claims, recommends technical focus areas)
9. Enriched Profile pushed as **note to Lever** (screening interviewer sees it) AND displayed in **Lauter candidate page** (HM sees it)
10. HM reviews enriched profile in Lauter → decides proceed to technical or reject

---

## Dependencies & Blockers

| Dependency | Owner | Status | Notes |
|------------|-------|--------|-------|
| Lever API access (read candidates/CVs, write notes, webhooks) | Head of IT | **Pending — blocker** | Need: API credentials, permission scope, webhook config |
| Barley API — confirm candidate email is available | Engineering | **Pending** | If no email, fallback to name + position + date matching (fragile, document risk) |
| Pilot positions selected | HM | **Pending** | 2-3 active positions with upcoming candidate flow |
| HR awareness | HR Lead | **Pending** | Not training — just heads-up that AI notes will appear in Lever |

---

## Stage 0: Integration Spikes

**Goal:** Prove both integrations work end-to-end before building pipeline logic.
**Gate:** If Lever API doesn't support webhooks or note writing → pivot (manual CV upload, notes via Slack/email)

### Lever Spike
- [ ] API access granted (sandbox if available)
- [ ] Confirm endpoints: read candidates, read CV/attachments, write notes, list stages
- [ ] Confirm webhook support for stage transitions (can we filter by position, or filter on our side?)
- [ ] Identify exact trigger stage name in Lever pipeline
- [ ] End-to-end proof: read a test candidate's CV → push a test note back
- [ ] Document rate limits, auth method, restrictions

### Barley Spike
- [ ] Confirm webhook payload structure (what fields? is it just a notification?)
- [ ] Confirm candidate email is available in Barley API response
- [ ] Query API by candidate identifier → retrieve transcript
- [ ] End-to-end proof: receive webhook → query → get transcript text
- [ ] Document matching strategy (email preferred, name + position + date fallback)

### Position Ingestion
- [ ] Ingest 2-3 pilot positions from Lever (manual or automated)
- [ ] Map Lever position data to Lauter position requirements format

---

## Stage 1: CV Brief Profile (Pre-Screening)

**Goal:** Automatically generate CV brief profile when candidate enters pipeline, push it to Lever before HR screens.
**Depends on:** Stage 0 completed

### Pipeline
- [ ] Lever webhook listener — receives stage transition events, filters to pilot positions
- [ ] Lever API client — read candidate data + CV/attachments for triggered candidates
- [ ] Decouple `cv_analysis` from `screening_eval` — cv_analysis runs independently at intake
- [ ] Redesign CV analysis prompt → gap analysis format:
  - Map skills/experience vs position must-haves and nice-to-haves
  - Flag gaps, inconsistencies, red flags
  - CV excerpts alongside assessments (verifiable claims)
  - Targeted screening questions for HR
- [ ] Calibrate prompts using 10-20 historical candidates (output structure + language tuning)
- [ ] Lever API client — push CV brief profile as note on candidate

### Data Model
- [ ] No schema changes — existing `Evaluation` with `step_type=cv_analysis` works
- [ ] Ensure cv_analysis can trigger without screening transcript

### Frontend
- [ ] None — HR sees note in Lever

**Validation:** HR confirms notes appear before screening. Quick feedback: useful or noise?

---

## Stage 2: Enriched Profile (Post-Screening)

**Goal:** After screening, automatically generate enriched profile and surface it to both HR (Lever) and HM (Lauter).
**Depends on:** Stage 1 live, Barley integration working

### Pipeline
- [ ] Barley webhook listener — receives recording-ready notifications
- [ ] Barley API client — match candidate (by email, fallback name + position + date), pull transcript
- [ ] Redesign screening_eval prompt → enriched profile format:
  - Takes CV brief profile as input (not just raw CV)
  - Cross-references screening findings against CV claims
  - Highlights remaining unknowns and risk areas
  - Recommends specific technical interview focus areas
- [ ] Push enriched profile as note to Lever (for screening interviewer / HR)

### Data Model
- [ ] Add `profile_viewed_at: datetime | None` to `CandidatePosition`
- [ ] Add `decision_made_at: datetime | None` to `CandidatePosition`
- [ ] Alembic migration for both fields

### Frontend (Lauter)
- [ ] Update candidate detail page — display enriched profile prominently
  - Structured sections: skills match, gaps, screening findings, recommended technical focus
  - Raw materials (CV, transcript) still accessible but secondary
- [ ] Track `profile_viewed_at` — set on page load of candidate with completed enriched profile
- [ ] Track `decision_made_at` — set on stage transition action (proceed to technical / reject)

**Validation:** HM debrief after first 5 candidates.

---

## Stage 3: Measurement & Kill Decision

**Goal:** After 10-15 candidates, decide if the pilot is worth continuing.
**Depends on:** Stage 2 live, sufficient candidate volume

### Deliverables
- [ ] Query: `decision_made_at - profile_viewed_at` delta per candidate
- [ ] Structured HM debrief (every 5 candidates):
  - Did you read the profile first?
  - Did it change or speed up your decision?
  - What was useless?
  - Did you still read raw CVs cover to cover?
- [ ] HR feedback (informal): Are the Lever notes useful? Do you use the screening questions?
- [ ] Go/no-go decision with data

### Decision Matrix

| Result | Action |
|--------|--------|
| HMs use profiles, decision time drops | Continue → plan scaling + Stage 3 feedback loop |
| HMs read profiles but still review raw materials | Iterate on profile quality, extend pilot |
| HMs ignore profiles | Kill — redirect effort |

---

## What's NOT in the Pilot

| Item | Why Parked | Revisit When |
|------|-----------|-------------|
| Process Feedback Loop | Cold start — most positions hire 1-2 people | Single position processes 5+ candidates |
| Technical eval (post-technical AI analysis) | Pilot focuses on pre-technical gate only | Pilot succeeds |
| Analytics dashboard | Overkill at pilot scale | Scaling beyond 2-3 positions |
| Full Lever ↔ Lauter sync | Pilot only reads CVs and writes notes | Lauter becomes primary tool |
| Recommendation / feedback generation | Existing feature, not in pilot scope | Post-pilot roadmap |

---

## Open Questions

1. What is the exact Lever stage name that triggers pre-screening? (ask HR)
2. Can Lever webhooks filter by position, or do we filter on our side? (Stage 0 spike)
3. Does Barley API response include candidate email? (Stage 0 spike)
4. Are there 2-3 positions with active candidate flow opening soon? (ask HM)
5. Position ingestion — manual (copy from Lever to Lauter) or build automated sync? (decide at Stage 0)
