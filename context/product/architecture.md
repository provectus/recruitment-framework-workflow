# System Architecture Overview: Recruitment Workflow POC

---

## 1. Workflow Orchestration & Automation

- **Workflow Engine:** n8n (self-hosted via Docker on ECS)

---

## 2. External Services & APIs

- **ATS (Applicant Tracking):** Lever API — pull candidate data, push evaluation notes back
- **Interview Transcription:** Metaview (manual export, no direct API integration)
- **AI Engine:** Claude via Amazon Bedrock — CV analysis, transcript processing, rubric evaluation, feedback generation
- **Team Communication:** Slack API — bot for transcript uploads and notifications

---

## 3. Input Mechanisms

- **Watched Folder:** AWS S3 (preferred) or Google Drive (alternative) — n8n monitors for new transcript uploads
- **Upload Interface:** Slack Bot — dedicated channel where HR and HMs can upload/paste transcripts

---

## 4. Data & Persistence

- **Primary Database:** PostgreSQL (AWS RDS) — stores evaluation history, candidate artifacts, and audit trail
- **Prompt Templates & Rubrics:** Version-controlled files in repository
- **Candidate Source of Truth:** Lever (synced, not duplicated)

**Data Model:**
```
Position (1) → Candidates (many)
Candidate (1) → Artifacts (many)
  - CV analysis result
  - Screening transcript + summary
  - Technical transcript + evaluation
  - Final recommendation
  - Feedback draft
```

---

## 5. Infrastructure & Deployment

- **Cloud Provider:** AWS
- **n8n Hosting:** ECS (Fargate) with Docker container
- **Database:** RDS PostgreSQL
- **File Storage:** S3

---

## 6. Observability & Monitoring

- **Logging:** CloudWatch Logs (captures n8n and workflow execution logs)
- **Metrics/Alerts:** CloudWatch Metrics (health monitoring, error alerts)
- **Workflow Debugging:** n8n built-in execution history
