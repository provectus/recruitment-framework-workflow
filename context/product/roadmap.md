# Product Roadmap: Recruitment Workflow POC

_This roadmap outlines our strategic direction based on customer needs and business goals. It focuses on the "what" and "why," not the technical "how."_

---

### Phase 1: Foundation

_The highest priority features that form the core foundation — getting data in and basic analysis working._

- [ ] **Input Mechanisms**
  - [ ] **Watched Folder Setup:** Configure Google Drive/Dropbox folder that n8n monitors for new transcript uploads
  - [ ] **Slack Bot for Uploads:** Create a Slack bot/channel where HR and HMs can paste or upload Metaview transcripts

- [ ] **Lever Integration (Read)**
  - [ ] **Candidate Data Pull:** Connect to Lever API to retrieve candidate profiles, resumes, and job requirements
  - [ ] **Job Requirements Extraction:** Parse role requirements to feed into the evaluation rubric

- [ ] **CV Analysis**
  - [ ] **Resume Parsing:** Extract key information from candidate CVs (experience, skills, education)
  - [ ] **Requirements Matching:** Compare CV data against role requirements, surface key signals and gaps

---

### Phase 2: Evaluation Pipeline

_Once data flows in, build the core evaluation and decision-support capabilities._

- [ ] **Screening Summary**
  - [ ] **Transcript Processing:** Ingest HR screening transcripts and extract structured insights
  - [ ] **HM-Ready Summary:** Generate concise summary highlighting key points for Hiring Manager review

- [ ] **Technical Evaluation**
  - [ ] **Technical Transcript Analysis:** Process technical interview transcripts against competency areas
  - [ ] **Decision Rubric Engine:** Apply weighted scoring framework with transparent reasoning for each criterion

- [ ] **Recommendation Generation**
  - [ ] **Hire/No-Hire Recommendation:** Generate structured recommendation with confidence level and supporting evidence
  - [ ] **Reasoning Transparency:** Clearly articulate why the system reached its conclusion

---

### Phase 3: Output & Feedback

_Complete the loop by pushing results back and generating candidate-facing feedback._

- [ ] **Lever Integration (Write)**
  - [ ] **Push Evaluation Notes:** Write AI-generated summaries and scores back to candidate profile in Lever
  - [ ] **Stage Update Suggestions:** Optionally suggest stage transitions based on evaluation outcome

- [ ] **Candidate Feedback Generation**
  - [ ] **Rejection Feedback Drafts:** Auto-generate professional, constructive feedback for rejected candidates
  - [ ] **Feedback Templates:** Create customizable templates for different rejection scenarios (skills gap, culture fit, etc.)
