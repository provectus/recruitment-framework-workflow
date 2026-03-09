# Functional Specification: Document Uploads (CV & Transcript)

- **Roadmap Item:** Web Application (SPA) → CV Upload + Transcript Upload
- **Status:** Completed
- **Author:** Nail

---

## 1. Overview and Rationale (The "Why")

The evaluation pipeline depends on candidate documents: CVs for resume analysis and interview transcripts for screening/technical evaluation. Without a way to get these documents into the system, none of the Phase 2 AI features (CV Analysis, Screening Summary, Technical Evaluation) can operate.

**Problem:** Candidates exist in the system with positions and pipeline stages, but there's no mechanism to attach the source material (resumes, interview transcripts) that downstream analysis depends on. Barley integration will eventually auto-sync transcripts, but it isn't built yet — manual upload is needed to unblock the evaluation pipeline now.

**Desired outcome:** Recruiters and hiring managers can upload CVs and interview transcripts through the SPA, associating them with the correct candidate and position. Documents are stored, versioned, and viewable in-app, ready for downstream AI processing.

**Success criteria:**
- Users can upload a CV (PDF/DOCX/MD) for any candidate-position pair
- Users can upload or paste interview transcripts for any candidate-position pair and interview stage
- Documents are viewable in-app by all authenticated users
- Upload history is preserved (replacing a document keeps previous versions accessible)
- Uploads are accessible from candidate detail pages and via a global quick action

---

## 2. Functional Requirements (The "What")

### 2.1 CV Upload

#### 2.1.1 Upload CV from Candidate Detail Page

- From the Candidate Detail page, for each linked position, the user can upload a CV.
- Each candidate-position pair supports one "current" CV with version history.
- **Accepted formats:** PDF, DOCX, MD
- **Max file size:** 25 MB
  - **Acceptance Criteria:**
    - [x] Each candidate-position row on the Candidate Detail page shows an "Upload CV" action (or the current CV filename if one exists)
    - [x] Clicking "Upload CV" opens a file picker supporting drag-and-drop
    - [x] Only PDF, DOCX, and MD files are accepted — other formats show: *"Unsupported file format. Please upload a PDF, DOCX, or MD file."*
    - [x] Files exceeding 25 MB are rejected with: *"File is too large. Maximum size is 25 MB."*
    - [x] After successful upload, the CV filename and upload date are displayed on the candidate-position row
    - [x] Upload shows a progress indicator for larger files

#### 2.1.2 CV Version History

- When a user uploads a new CV for a candidate-position pair that already has one, the new CV becomes the "current" version and the previous version is preserved.
  - **Acceptance Criteria:**
    - [x] Uploading a new CV when one already exists does NOT require confirmation — the new version simply becomes current
    - [x] A "Version history" action is available for each CV, showing a list of all previously uploaded versions with filename, upload date, and uploader name
    - [x] Any version from the history can be viewed in-app
    - [x] The most recent version is displayed by default

#### 2.1.3 View CV In-App

- Clicking on a CV opens an in-app viewer. Documents are view-only (no download).
  - **Acceptance Criteria:**
    - [x] PDF files render in an embedded PDF viewer
    - [x] DOCX and MD files render as formatted text in-app
    - [x] The viewer displays the filename, upload date, and uploader name
    - [x] The viewer can be closed to return to the previous page

### 2.2 Transcript Upload

#### 2.2.1 Upload or Paste Transcript from Candidate Detail Page

- From the Candidate Detail page, for each linked position, the user can upload or paste an interview transcript.
- Each transcript is associated with an interview stage (screening or technical) and includes metadata.
- Multiple transcripts per stage are allowed (e.g., multiple technical interview rounds).
- **File upload formats:** PDF, TXT, DOCX, MD
- **Paste input:** Plain text
- **Max file size:** 25 MB
- **Required metadata:** Interview stage (screening/technical), interviewer name (selected from Tap users), interview date
- **Optional metadata:** Notes (free text)
  - **Acceptance Criteria:**
    - [x] The Candidate Detail page has an "Add Transcript" action for each linked position
    - [x] Clicking "Add Transcript" opens a dialog/form with two input modes: "Upload File" tab and "Paste Text" tab
    - [x] **File upload tab:** drag-and-drop or file picker for PDF, TXT, DOCX, MD (same format/size validation as CV)
    - [x] **Paste text tab:** a plain text area where the user can paste transcript content directly
    - [x] The form requires: interview stage dropdown (Screening / Technical), interviewer dropdown (populated from Tap users), interview date picker
    - [x] The form includes an optional "Notes" text field
    - [x] After successful submission, the transcript appears in a transcript list for that candidate-position pair, grouped by stage

#### 2.2.2 Multiple Transcripts Per Stage

- A candidate-position pair can have multiple transcripts for the same stage (e.g., two technical rounds with different interviewers).
  - **Acceptance Criteria:**
    - [x] The transcript list for a candidate-position pair shows all transcripts, grouped or labeled by stage
    - [x] Each transcript entry displays: stage, interviewer name, interview date, upload date, input method (file or paste)
    - [x] Transcripts are ordered by interview date (most recent first) within each stage group

#### 2.2.3 View Transcript In-App

- Clicking on a transcript opens an in-app viewer. View-only (no download).
  - **Acceptance Criteria:**
    - [x] File-based transcripts render the same way as CVs (PDF viewer, formatted text for TXT/DOCX/MD)
    - [x] Pasted transcripts display as plain text
    - [x] The viewer shows metadata: stage, interviewer, interview date, notes (if any), upload date, uploader
    - [x] The viewer can be closed to return to the previous page

### 2.3 Global Quick Action

- A persistent "+" button in the app header/sidebar provides quick access to upload actions from anywhere in the app.
  - **Acceptance Criteria:**
    - [x] A "+" button is visible in the app header or sidebar on all authenticated pages
    - [x] Clicking it opens a menu with two options: "Upload CV" and "Upload Transcript"
    - [x] **"Upload CV"** opens a dialog that first asks the user to select a candidate, then a position (from that candidate's linked positions), then the file upload
    - [x] **"Upload Transcript"** opens a dialog that first asks the user to select a candidate, then a position, then the transcript form (same as 2.2.1)
    - [x] Candidate and position selectors support search/typeahead for quick selection
    - [x] After successful upload, the user can navigate to the candidate detail page or dismiss the dialog

### 2.4 Upload from Interview Library

- The Interview Library page (a separate roadmap item that lists all interviews) should also allow transcript upload. [NEEDS CLARIFICATION: Since the Interview Library spec doesn't exist yet, the exact integration point will be defined in that spec. This spec establishes the upload components as reusable so the Interview Library can consume them.]

### 2.5 Candidate Detail — Documents Section

- The Candidate Detail page gains a documents section showing all uploads for the selected candidate across all positions.
  - **Acceptance Criteria:**
    - [x] The Candidate Detail page includes a "Documents" section (or tab) below the positions section
    - [x] For each position, CVs and transcripts are listed with type label, filename/stage, date, and uploader
    - [x] Clicking any document opens the in-app viewer
    - [x] Empty state: *"No documents uploaded yet. Upload a CV or transcript to get started."*

### 2.6 Bulk Upload

- Users can select or drag-and-drop multiple files at once in any upload dialog. All files go to the same candidate-position (and same stage, for transcripts).
  - **Acceptance Criteria:**
    - [x] File picker and drag-and-drop zone accept multiple files simultaneously
    - [x] Each file is validated independently (format, size) — invalid files are flagged without blocking valid ones
    - [x] A summary is shown before confirming: list of files with status (valid / invalid with reason)
    - [x] For CV bulk upload: each file becomes a separate version in chronological order (last file in the batch = current version)
    - [x] For transcript bulk upload: each file creates a separate transcript entry, all sharing the same metadata (stage, interviewer, date) from the form
    - [x] Progress is shown per-file during upload
    - [x] If some files fail, successful uploads are kept and failures are reported: *"N of M files uploaded successfully. Failed: [filenames with reasons]."*

---

## 3. Scope and Boundaries

### In-Scope

- CV file upload (PDF, DOCX, MD) per candidate-position pair with version history
- Transcript upload (file: PDF, TXT, DOCX, MD) and paste (plain text) per candidate-position-stage with metadata (interviewer, date, notes)
- Multiple transcripts per stage per candidate-position
- Bulk upload (multiple files in one drop) for both CVs and transcripts
- In-app document viewer (view-only, no download)
- Global "+" quick action for uploads from any page
- Document storage in S3 (files bucket)
- Documents section on Candidate Detail page

### Out-of-Scope

- **The following are separate roadmap items and will be addressed in their own specs:**
  - Interview Library & Recording/Transcript Viewer (separate spec — transcript upload components will be reusable)
  - Barley Integration (S3 transcript sync — automated, not manual upload)
  - CV Analysis / Resume Parsing (consumes uploaded CVs, separate roadmap item)
  - Screening Summary / Technical Evaluation (consumes uploaded transcripts, Phase 2)
  - n8n Integration (workflow triggers, separate roadmap item)
  - Lever Integration (read/write, deferred)
  - Candidate Feedback Generation (Phase 3)
- **Deferred features within this domain:**
  - File download (view-only for POC)
  - Drag-and-drop reordering of transcripts
  - OCR or text extraction from scanned PDFs
  - Rich text / markdown editor for pasted transcripts (plain text only)
