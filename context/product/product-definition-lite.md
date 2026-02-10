# Recruitment Workflow POC — Summary

## Vision

Automate the candidate evaluation workflow by connecting Lever (sourcing), Barley (interview recording and transcription), and Claude AI (decision framework), eliminating manual data transfer and enabling faster, more consistent hiring decisions.

## Target Audience

- **Primary:** Hiring Managers and Engineering Managers at Provectus
- **Secondary:** HR Recruiters (for managing recruitment pipeline and reviewing screening results)

## Core Features

- **Interview Library** — Centralized page to browse, search, and access all Barley-recorded recruitment interviews
- **Barley Integration** — Sync recordings and transcripts from Barley's S3 storage, filtered to recruitment only
- **CV Analysis** — Parse resume against role requirements
- **Screening Summary** — Process HR screening transcript (from Barley) for HM review
- **Technical Evaluation** — Analyze technical interview against competency rubric
- **Decision Rubric** — Weighted scoring with transparent reasoning
- **Candidate Feedback** — Auto-generate rejection feedback
- **Lever Integration** — Push AI-generated notes back to candidate profile

## Key Constraints

- Barley S3 bucket structure and access pattern TBD — sync with Barley team required
- Recruitment interviews must be filtered from all company calls
- Decision authority remains with Hiring Manager
