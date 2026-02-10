# Product Roadmap: Recruitment Workflow POC

_This roadmap outlines our strategic direction based on customer needs and business goals. It focuses on the "what" and "why," not the technical "how."_

---

### Phase 0: Infrastructure

_Technical prerequisites that must be in place before product features can be built and deployed._

- [ ] **AWS Environment**
  - [ ] **Cloud Setup:** VPC, subnets, ECS cluster, RDS PostgreSQL, S3, CloudWatch — the runtime environment for API and SPA
  - [ ] **Bedrock Access:** Enable Claude model access in us-east-1

- [ ] **n8n Instance (On-Prem)**
  - [ ] **Dedicated Instance Setup:** Docker Compose with n8n + its own Postgres on the purchased instance
  - [ ] **Connectivity:** Establish outbound HTTPS from on-prem to AWS services (direct internet or VPN — TBD with ops)

- [ ] **CI/CD & Deployment**
  - [ ] **Pipeline Setup:** Automated build and deploy for FastAPI (ECS) and React SPA (S3 + CloudFront)

---

### Phase 1: Foundation

_The core foundation — a working web application where recruiters can log in, manage candidates, upload documents, and trigger initial analysis._

- [ ] **Web Application (SPA)**
  - [ ] **Authentication:** Google OAuth 2.0 login for recruiters and hiring managers
  - [ ] **Candidate List:** View candidates synced from Lever with evaluation status and progress tracking
  - [ ] **Interview Library:** Dedicated page listing all Barley-recorded recruitment interviews with candidate name, position, date, and interviewer — browse, search, and access recordings and transcripts in one place
  - [ ] **Recording & Transcript Viewer:** Click into any interview to access recording playback and full transcript, replacing scattered Slack chat threads
  - [ ] **CV Upload:** Drag-and-drop upload of CVs, associated with a candidate and position
  - [ ] **Position/Job Selector:** Browse and select open positions (pulled from Lever)

- [ ] **Backend API**
  - [ ] **Core API:** FastAPI service handling auth, uploads, candidate data, and evaluation orchestration
  - [ ] **n8n Integration:** Webhook triggers from API to n8n for kicking off evaluation workflows

- [ ] **Barley Integration**
  - [ ] **S3 Transcript Sync:** Read interview transcripts and recordings from Barley's S3 storage (exact bucket structure and access pattern TBD — sync with Barley team required)
  - [ ] **Recruitment Filter:** Filter Barley data to recruitment interviews only — exclude non-recruitment company calls
  - [ ] **Candidate & Position Linking:** Associate each Barley interview with the correct candidate and position in our system

- [ ] **Lever Integration (Read)**
  - [ ] **Candidate Data Pull:** Connect to Lever API to retrieve candidate profiles, resumes, and job requirements
  - [ ] **Job Requirements Extraction:** Parse role requirements to feed into the evaluation rubric

- [ ] **CV Analysis**
  - [ ] **Resume Parsing:** Extract key information from candidate CVs (experience, skills, education)
  - [ ] **Requirements Matching:** Compare CV data against role requirements, surface key signals and gaps

---

### Phase 2: Evaluation Pipeline

_Build the core evaluation and decision-support capabilities, from screening through to final recommendation._

- [ ] **Screening Summary**
  - [ ] **Transcript Processing:** Ingest HR screening transcripts from Barley and extract structured insights
  - [ ] **HM-Ready Summary:** Generate concise summary highlighting key points for Hiring Manager review

- [ ] **HM Review & Decision Gate**
  - [ ] **Screening Results View:** Display AI-generated screening summary alongside candidate profile in the SPA
  - [ ] **Proceed/Reject Decision:** Allow HM to mark candidate as "proceed to technical" or "reject" with optional notes
  - [ ] **Rejection Triggers Feedback Flow:** When rejected at this stage, trigger candidate feedback generation

- [ ] **Technical Evaluation**
  - [ ] **Technical Transcript Analysis:** Process technical interview transcripts (from Barley) against competency areas
  - [ ] **Decision Rubric Engine:** Apply weighted scoring framework with transparent reasoning for each criterion

- [ ] **Recommendation Generation**
  - [ ] **Hire/No-Hire Recommendation:** Generate structured recommendation with confidence level and supporting evidence
  - [ ] **Reasoning Transparency:** Clearly articulate why the system reached its conclusion

---

### Phase 3: Output & Feedback

_Complete the loop by pushing results back to Lever and generating candidate-facing feedback._

- [ ] **Lever Integration (Write)**
  - [ ] **Push Evaluation Notes:** Write AI-generated summaries and scores back to candidate profile in Lever
  - [ ] **Stage Update Suggestions:** Optionally suggest stage transitions based on evaluation outcome

- [ ] **Candidate Feedback Generation**
  - [ ] **Rejection Feedback Drafts:** Auto-generate professional, constructive feedback for rejected candidates
  - [ ] **Feedback Templates:** Create customizable templates for different rejection scenarios (skills gap, culture fit, etc.)
