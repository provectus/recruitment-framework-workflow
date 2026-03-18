# Product Roadmap: Recruitment Workflow — Lauter

_This roadmap outlines our strategic direction based on customer needs and business goals. It focuses on the "what" and "why," not the technical "how."_

---

### Phase 0: Infrastructure

_Technical prerequisites that must be in place before product features can be built and deployed._

- [x] **AWS Environment**
  - [x] **Cloud Setup:** VPC, subnets, ECS cluster, RDS PostgreSQL, S3, CloudWatch — the runtime environment for API and SPA
  - [x] **Bedrock Access:** Enable Claude model access in us-east-1

- [x] ~~**n8n Instance (On-Prem)**~~ **Replaced by Lambda + Step Functions (v5.0)**
  - [x] ~~Dedicated Instance Setup~~ — Lambda + Step Functions replaces n8n
  - [x] ~~Connectivity~~ — All within AWS, no on-prem needed

- [x] **CI/CD & Deployment**
  - [x] **Pipeline Setup:** Automated build and deploy for FastAPI (ECS) and React SPA (S3 + CloudFront)

---

### Phase 1: Foundation

_The core foundation — a working web application where recruiters can log in, manually manage candidates and positions, upload documents, and trigger initial analysis._

- [ ] **Web Application (SPA)**
  - [x] **Authentication:** Google OAuth 2.0 login for recruiters and hiring managers
  - [x] **Candidate Management:** Create, view, and edit candidates manually — name, contact info, status tracking
  - [x] **Position Management:** Create and manage open positions with requirements, team, and hiring manager
  - [x] **Candidate List:** View candidates with evaluation status and progress tracking
  - [ ] **Interview Library:** Dedicated page listing all recruitment interviews with candidate name, position, date, and interviewer — browse, search, and access recordings and transcripts in one place
  - [ ] **Recording & Transcript Viewer:** Click into any interview to access recording playback and full transcript
  - [x] **CV Upload:** Drag-and-drop upload of CVs, associated with a candidate and position
  - [x] **Transcript Upload:** Manual upload or paste of interview transcripts per candidate and interview stage — ensures the evaluation pipeline works independently of Barley

- [ ] **Backend API**
  - [ ] **Core API:** FastAPI service handling auth, uploads, candidate data, and evaluation orchestration
  - [x] ~~**n8n Integration**~~ **Replaced:** EventBridge triggers from API to Step Functions (v5.0)

- [x] **Lever API Research**
  - [x] **API Exploration:** Investigate Lever API auth model (OAuth 2.0 / API keys), available endpoints, rate limits, webhook support, and data schemas — document findings for integration planning
  - [x] **Integration Strategy:** Define sync approach (polling vs webhooks), data mapping between Lever and our models, error handling, and pagination strategy
  - [x] **Feedback Form Endpoints:** Investigate how Lever structures feedback forms per posting/stage — field types, rating scales, required vs optional fields, and interviewer assignment model

- [x] **CV Analysis**
  - [x] **Resume Parsing:** Extract key information from candidate CVs (experience, skills, education)
  - [x] **Requirements Matching:** Compare CV data against role requirements, surface key signals and gaps

---

### Phase 2: Evaluation Pipeline

_Build the core evaluation and decision-support capabilities, from screening through to final recommendation. Results are displayed in the SPA; Lever write-back is deferred to the Future phase._

- [x] **Screening Summary**
  - [x] **Transcript Processing:** Ingest HR screening transcripts (from Barley sync or manual upload) and extract structured insights
  - [x] **HM-Ready Summary:** Generate concise summary highlighting key points for Hiring Manager review

- [x] **HM Review & Decision Gate**
  - [x] **Screening Results View:** Display AI-generated screening summary alongside candidate profile in the SPA
  - [x] **Proceed/Reject Decision:** Allow HM to mark candidate as "proceed to technical" or "reject" with optional notes
  - [x] **Rejection Triggers Feedback Flow:** When rejected at this stage, trigger candidate feedback generation

- [x] **Technical Evaluation**
  - [x] **Technical Transcript Analysis:** Process technical interview transcripts (from Barley sync or manual upload) against competency areas
  - [x] **Decision Rubric Engine:** Apply weighted scoring framework with transparent reasoning for each criterion
    - [x] Rubric management: templates, position rubrics, versioning, editor (spec 006)

- [x] **Recommendation Generation**
  - [x] **Hire/No-Hire Recommendation:** Generate structured recommendation with confidence level and supporting evidence
  - [x] **Reasoning Transparency:** Clearly articulate why the system reached its conclusion

- [ ] **Candidate Feedback Generation**
  - [x] **Rejection Feedback Drafts:** Auto-generate professional, constructive feedback for rejected candidates (implemented in spec 007)
  - [ ] **Feedback Templates:** Create customizable templates for different rejection scenarios (skills gap, culture fit, etc.)

---

### Pilot Pivot: Candidate Profiling

_Strategic pivot based on demo feedback and problem reframing. The POC evaluation pipeline works, but wasn't aimed at the right pain point. The real problem: HMs spend too much time reviewing raw materials and still end up in technical interviews with mismatched candidates. This pivot reorients existing AI capabilities toward two-stage candidate profiling with Lever + Barley integration — no workflow change for HR, structured insight for HMs. See `context/product/problem-statement.md` and `context/product/pilot-plan.md` for full context._

_**Scope:** 2-3 positions, ~10-15 candidates. **Kill criterion:** If HMs ignore profiles after 10-15 candidates → pull the plug._

- [ ] **Pilot Stage 0: Integration Spikes**
  - [ ] **Lever Integration (pilot scope: read candidates/CVs, write notes, receive webhooks):** API access, confirm endpoints, webhook support for stage transitions, end-to-end proof (read test CV → push test note). Full Lever sync (feedback forms, stage updates) remains deferred.
  - [ ] **Barley Integration (pilot scope: receive webhook notifications, query transcripts by candidate):** Confirm webhook payload, confirm candidate email available for matching, end-to-end proof (receive webhook → query → get transcript). Full Barley sync (recording library, playback) remains deferred.
  - [ ] **Pilot Position Ingestion:** Ingest 2-3 positions from Lever (manual or automated), map to Lauter position requirements format

- [ ] **Pilot Stage 1: CV Brief Profile (Pre-Screening)**
  - [ ] **Lever Webhook Listener:** Receive stage transition events (e.g., "New Applicant"), filter to pilot positions only
  - [ ] **CV Ingestion from Lever:** Pull candidate data + CV/attachments via Lever API for triggered candidates
  - [ ] **CV Analysis Redesign:** Decouple cv_analysis from screening_eval — runs independently at intake. Redesign prompt from generic summary to gap analysis: skills vs requirements, flag gaps/red flags, CV excerpts alongside assessments, targeted screening questions for HR
  - [ ] **Prompt Calibration:** Tune output structure and language using 10-20 historical candidates (calibration, not validation)
  - [ ] **Push CV Brief Profile to Lever:** Write AI-generated profile as a note on the candidate in Lever — HR sees it before scheduling screening, no workflow change

- [ ] **Pilot Stage 2: Enriched Profile (Post-Screening)**
  - [ ] **Barley Webhook Listener:** Receive recording-ready notifications, match to candidate by email (fallback: name + position + date)
  - [ ] **Transcript Ingestion from Barley:** Query Barley API, pull screening transcript for matched candidate
  - [ ] **Enriched Profile Generation:** Redesign screening_eval prompt — takes CV brief profile as input, cross-references screening findings against CV claims, highlights remaining unknowns, recommends technical interview focus areas
  - [ ] **Push Enriched Profile to Lever:** Write enriched profile as note on candidate in Lever (for HR / screening interviewer)
  - [ ] **Enriched Profile in Lauter:** Update candidate detail page — display enriched profile prominently with structured sections (skills match, gaps, screening findings, recommended technical focus). Raw materials remain accessible but secondary.
  - [ ] **Measurement Tracking:** Add `profile_viewed_at` and `decision_made_at` to candidate-position model. Track when HM opens profile and when they make a stage transition decision.

- [ ] **Pilot Stage 3: Measurement & Kill Decision**
  - [ ] **Decision Acceleration Query:** Report `decision_made_at - profile_viewed_at` delta per candidate
  - [ ] **Structured HM Debrief:** Every 5 candidates — did profiles change or speed up decisions? What was useless? Still reading raw CVs?
  - [ ] **HR Feedback:** Informal — are Lever notes useful? Are screening questions used?
  - [ ] **Go/No-Go Decision:** Kill, iterate, or scale based on data

---

### Future: Post-Pilot Scaling

_Revisit after pilot validates the candidate profiling approach. Timing depends on pilot results._

- [ ] **Process Feedback Loop**
  - [ ] **Post-Outcome Analysis:** After each hire/reject outcome, analyze whether AI profiles surfaced the right signals — refine prompts and screening questions for the next candidate on the same position
  - [ ] **Interviewer Effectiveness:** Evaluate whether screening and technical interviews covered AI-recommended focus areas

- [ ] **Full Lever Integration**
  - [ ] **Candidate Data Pull:** Full sync of candidate profiles, resumes, and job requirements
  - [ ] **Feedback Form Schema Pull:** Retrieve feedback form templates and fields per position and interview stage
  - [ ] **Push Evaluation Notes:** Write AI-generated summaries and scores back to candidate profile in Lever
  - [ ] **Approved Feedback Submission:** Push reviewer-approved feedback forms back to Lever per interviewer assignee
  - [ ] **Stage Update Suggestions:** Optionally suggest stage transitions based on evaluation outcome

- [ ] **Full Barley Integration**
  - [ ] **Interview Library:** Centralized page listing all recruitment interviews with search, recording playback, and full transcript access
  - [ ] **S3 Transcript Sync:** Read interview transcripts and recordings from Barley's S3 storage
  - [ ] **Recruitment Filter:** Filter Barley data to recruitment interviews only

- [ ] **Feedback Form Drafting & Review**
  - [ ] **AI Feedback Drafting:** LLM fills in Lever feedback form fields based on interview transcript analysis — generates draft per interviewer assignee for both recruitment and technical stages
  - [ ] **Review & Approval UI:** Reviewer sees AI-drafted feedback in the SPA, can edit any field, and explicitly approves before submission to Lever

- [ ] **AI Candidate Analyst (Chat)**
  - [ ] **Conversational Interface:** Chat widget in the SPA for recruiters to ask questions about a candidate in natural language
  - [ ] **Agent Backend:** Long-running Agent SDK service (ECS Fargate) with custom MCP tools for querying evaluations, fetching CVs/transcripts, searching candidates, and retrieving position details
  - [ ] **Session Persistence:** Recruiter can leave and resume a conversation with full context retained
  - [ ] **Cross-Signal Synthesis:** Answer questions that span multiple evaluation steps
  - [ ] **Candidate Comparison:** Compare candidates against each other or against position requirements on demand
