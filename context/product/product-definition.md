# Product Definition: Recruitment Workflow POC

- **Version:** 1.0
- **Status:** Proposed

---

## 1. The Big Picture (The "Why")

### 1.1. Project Vision & Purpose

To automate the candidate evaluation workflow by connecting Lever (sourcing), Barley (interview recording and transcription), and Claude AI (decision framework), eliminating manual data transfer where possible and enabling faster, more consistent hiring decisions.

### 1.2. Target Audience

Hiring Managers and Engineering Managers at Provectus who evaluate candidates based on interview feedback. HR team members are also involved in the workflow for managing the recruitment pipeline and reviewing screening results.

### 1.3. User Personas

- **Persona 1: "Jordan the Engineering Manager"**
  - **Role:** Engineering Manager at Provectus responsible for hiring decisions
  - **Goal:** Make consistent, well-informed hiring decisions quickly by having structured candidate data and interview insights readily available
  - **Frustration:** Interview recordings and transcripts from Barley end up scattered across Slack chats, making it hard to find the right one; must then manually cross-reference with job requirements and apply a decision framework in Claude — all repetitive and slows down the hiring pipeline

- **Persona 2: "Sam the HR Recruiter"**
  - **Role:** HR Recruiter at Provectus conducting initial candidate screenings
  - **Goal:** Pass relevant screening insights to Hiring Managers efficiently without lengthy handoff meetings
  - **Frustration:** Barley sends interview summaries to Slack chats alongside unrelated candidates, creating a mess; screening notes and context often get lost or require manual summarization before handoff

### 1.4. Success Metrics

- **Streamlined evaluation pipeline:** Better filtering at each stage (CV analysis → screening → technical) using a weighted decision rubric
- **Reduced manual work:** Eliminate copy-paste and repetitive data transfer tasks wherever possible
- **Hiring quality:** Successful hires who pass their probation period

---

## 2. The Product Experience (The "What")

### 2.1. Core Features

- **Interview Library** — Centralized web page listing all Barley-recorded recruitment interviews with search, recording playback, and full transcript access
- **Barley Integration** — Sync interview recordings and transcripts from Barley's S3 storage, filtered to recruitment interviews only
- **CV Analysis** — Parse resume against role requirements, surface key signals and potential red flags
- **Screening Summary** — Process HR screening transcript (from Barley), extract relevant insights for HM review
- **Technical Evaluation** — Analyze technical interview transcript (from Barley) against competency rubric
- **Decision Rubric Engine** — Apply weighted scoring framework, generate recommendation with clear reasoning
- **Candidate Feedback Generation** — Auto-generate structured, candidate-facing feedback (especially for rejections)
- **Lever Integration** — Pull candidate/job data, push AI-generated notes and summaries back to candidate profile

### 2.2. User Journey

1. **Sourcing:** Candidate is sourced and enters pipeline in Lever
2. **HR Screening:** HR conducts screening call; Barley joins and records the interview, storing transcript in S3
3. **Interview Available:** Interview appears in the Interview Library — recruiter or HM can access recording and transcript at any time
4. **Screening Analysis:** System processes Barley transcript and generates summary with key insights for HM
5. **HM Review:** Hiring Manager reviews candidate profile + AI-generated screening summary; decides to proceed or reject
6. **Technical Interview:** HM conducts technical interview; Barley joins and records the interview, storing transcript in S3
7. **Evaluation & Recommendation:** System applies weighted rubric, generates recommendation with reasoning + draft candidate feedback
8. **Decision:** HM reviews recommendation, makes final hire/no-hire decision
9. **Lever Update:** System pushes notes and evaluation summary back to Lever; feedback sent to candidate if rejected

---

## 3. Project Boundaries

### 3.1. What's In-Scope for this Version

- CV parsing and analysis against role requirements
- CV upload via web SPA (React + TypeScript)
- Barley integration (read interview recordings and transcripts from Barley's S3 storage)
- Interview Library — centralized web page to browse, search, and access all recruitment interviews
- Weighted decision rubric with transparent reasoning
- Candidate feedback generation (for rejections)
- Lever integration (read candidate data, push notes/summaries)
- n8n workflow orchestration connecting all services
- Claude AI as the evaluation and decision-support engine

### 3.2. What's Out-of-Scope (Non-Goals)

- Multi-company/tenant support
- Automated candidate communication (sending emails directly)
- Calendar/scheduling integration
- Mobile application
