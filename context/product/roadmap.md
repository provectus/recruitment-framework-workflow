# Product Roadmap: Recruitment Workflow POC

_This roadmap outlines our strategic direction based on customer needs and business goals. It focuses on the "what" and "why," not the technical "how."_

---

### Phase 0: Infrastructure

_Technical prerequisites that must be in place before product features can be built and deployed._

- [x] **AWS Environment**
  - [x] **Cloud Setup:** VPC, subnets, ECS cluster, RDS PostgreSQL, S3, CloudWatch — the runtime environment for API and SPA
  - [x] **Bedrock Access:** Enable Claude model access in us-east-1

- [ ] **n8n Instance (On-Prem)**
  - [ ] **Dedicated Instance Setup:** Docker Compose with n8n + its own Postgres on the purchased instance
  - [ ] **Connectivity:** Establish outbound HTTPS from on-prem to AWS services (direct internet or VPN — TBD with ops)

- [x] **CI/CD & Deployment**
  - [x] **Pipeline Setup:** Automated build and deploy for FastAPI (ECS) and React SPA (S3 + CloudFront)

---

### Phase 1: Foundation

_The core foundation — a working web application where recruiters can log in, manually manage candidates and positions, upload documents, and trigger initial analysis. Barley integration runs in parallel; Lever integration is deferred to keep the POC self-contained._

- [ ] **Web Application (SPA)**
  - [x] **Authentication:** Google OAuth 2.0 login for recruiters and hiring managers
  - [ ] **Candidate Management:** Create, view, and edit candidates manually — name, contact info, status tracking
  - [ ] **Position Management:** Create and manage open positions with requirements, team, and hiring manager
  - [ ] **Candidate List:** View candidates with evaluation status and progress tracking
  - [ ] **Interview Library:** Dedicated page listing all recruitment interviews with candidate name, position, date, and interviewer — browse, search, and access recordings and transcripts in one place
  - [ ] **Recording & Transcript Viewer:** Click into any interview to access recording playback and full transcript
  - [ ] **CV Upload:** Drag-and-drop upload of CVs, associated with a candidate and position
  - [ ] **Transcript Upload:** Manual upload or paste of interview transcripts per candidate and interview stage — ensures the evaluation pipeline works independently of Barley

- [ ] **Backend API**
  - [ ] **Core API:** FastAPI service handling auth, uploads, candidate data, and evaluation orchestration
  - [ ] **n8n Integration:** Webhook triggers from API to n8n for kicking off evaluation workflows

- [x] **Lever API Research**
  - [x] **API Exploration:** Investigate Lever API auth model (OAuth 2.0 / API keys), available endpoints, rate limits, webhook support, and data schemas — document findings for integration planning
  - [x] **Integration Strategy:** Define sync approach (polling vs webhooks), data mapping between Lever and our models, error handling, and pagination strategy
  - [x] **Feedback Form Endpoints:** Investigate how Lever structures feedback forms per posting/stage — field types, rating scales, required vs optional fields, and interviewer assignment model

- [ ] **Barley Integration**
  - [ ] **S3 Transcript Sync:** Read interview transcripts and recordings from Barley's S3 storage (exact bucket structure and access pattern TBD — sync with Barley team required)
  - [ ] **Recruitment Filter:** Filter Barley data to recruitment interviews only — exclude non-recruitment company calls
  - [ ] **Candidate & Position Linking:** Associate each Barley interview with the correct candidate and position in our system

- [ ] **CV Analysis**
  - [ ] **Resume Parsing:** Extract key information from candidate CVs (experience, skills, education)
  - [ ] **Requirements Matching:** Compare CV data against role requirements, surface key signals and gaps

---

### Phase 2: Evaluation Pipeline

_Build the core evaluation and decision-support capabilities, from screening through to final recommendation. Results are displayed in the SPA; Lever write-back is deferred to the Future phase._

- [ ] **Screening Summary**
  - [ ] **Transcript Processing:** Ingest HR screening transcripts (from Barley sync or manual upload) and extract structured insights
  - [ ] **HM-Ready Summary:** Generate concise summary highlighting key points for Hiring Manager review

- [ ] **HM Review & Decision Gate**
  - [ ] **Screening Results View:** Display AI-generated screening summary alongside candidate profile in the SPA
  - [ ] **Proceed/Reject Decision:** Allow HM to mark candidate as "proceed to technical" or "reject" with optional notes
  - [ ] **Rejection Triggers Feedback Flow:** When rejected at this stage, trigger candidate feedback generation

- [ ] **Technical Evaluation**
  - [ ] **Technical Transcript Analysis:** Process technical interview transcripts (from Barley sync or manual upload) against competency areas
  - [ ] **Decision Rubric Engine:** Apply weighted scoring framework with transparent reasoning for each criterion

- [ ] **Recommendation Generation**
  - [ ] **Hire/No-Hire Recommendation:** Generate structured recommendation with confidence level and supporting evidence
  - [ ] **Reasoning Transparency:** Clearly articulate why the system reached its conclusion

---

### Phase 3: Candidate Feedback

_Generate candidate-facing feedback to close the loop on rejected candidates._

- [ ] **Candidate Feedback Generation**
  - [ ] **Rejection Feedback Drafts:** Auto-generate professional, constructive feedback for rejected candidates
  - [ ] **Feedback Templates:** Create customizable templates for different rejection scenarios (skills gap, culture fit, etc.)

---

### Future: Lever Integration

_Deferred until the POC evaluation pipeline is proven. No specific phase assigned — timing depends on POC results and Lever access readiness._

- [ ] **Lever Integration (Read)**
  - [ ] **Candidate Data Pull:** Connect to Lever API to retrieve candidate profiles, resumes, and job requirements
  - [ ] **Job Requirements Extraction:** Parse role requirements to feed into the evaluation rubric
  - [ ] **Feedback Form Schema Pull:** Retrieve feedback form templates and fields per position and interview stage (recruitment + technical), including assigned interviewer

- [ ] **Lever Integration (Write)**
  - [ ] **Push Evaluation Notes:** Write AI-generated summaries and scores back to candidate profile in Lever
  - [ ] **Approved Feedback Submission:** Push reviewer-approved feedback forms back to Lever per interviewer assignee
  - [ ] **Stage Update Suggestions:** Optionally suggest stage transitions based on evaluation outcome

- [ ] **Feedback Form Drafting & Review**
  - [ ] **AI Feedback Drafting:** LLM fills in Lever feedback form fields based on interview transcript analysis — generates draft per interviewer assignee for both recruitment and technical stages
  - [ ] **Review & Approval UI:** Reviewer sees AI-drafted feedback in the SPA, can edit any field, and explicitly approves before submission to Lever
