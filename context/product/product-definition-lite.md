# Recruitment Workflow POC — Summary

## Vision

Automate the candidate evaluation workflow by connecting Lever (sourcing), Metaview (interview transcription), and Claude AI (decision framework), eliminating manual data transfer and enabling faster, more consistent hiring decisions.

## Target Audience

- **Primary:** Hiring Managers and Engineering Managers at Provectus
- **Secondary:** HR Recruiters (for transcript uploads and screening handoffs)

## Core Features

- **CV Analysis** — Parse resume against role requirements
- **Screening Summary** — Process HR screening transcript for HM review
- **Technical Evaluation** — Analyze technical interview against competency rubric
- **Decision Rubric** — Weighted scoring with transparent reasoning
- **Candidate Feedback** — Auto-generate rejection feedback
- **Lever Integration** — Push AI-generated notes back to candidate profile

## Key Constraints

- Metaview transcripts require manual upload (via Slack bot or watched folder)
- No web UI — orchestration via n8n workflows
- Decision authority remains with Hiring Manager
