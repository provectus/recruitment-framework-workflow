# Technical Specification: Document Uploads (CV & Transcript)

- **Functional Specification:** `context/spec/005-document-uploads/functional-spec.md`
- **Status:** Completed
- **Author(s):** Nail

---

## 1. High-Level Technical Approach

This feature adds document upload and viewing for CVs and interview transcripts, associated with candidate-position pairs. It spans backend and frontend:

- **Backend:** 1 new SQLModel model (`Document`) with a `type` discriminator (cv/transcript) and nullable transcript-specific metadata fields. 2 new services: `storage_service.py` (S3 presigned URL generation) and `document_service.py` (upload orchestration, version management, queries). 1 new router under `/api/documents`. S3 integration via `aioboto3`.

- **Frontend:** New `features/documents/` module with TanStack Query hooks. New widget components: drag-drop upload zone, document list, in-app viewer (PDF via embed, DOCX via mammoth.js, MD via react-markdown). Integration into Candidate Detail page (Documents section) and app shell (global "+" quick action).

- **Upload flow:** Two-step presigned URL pattern — frontend requests a presigned S3 PUT URL from backend, uploads directly to S3, then confirms completion. Pasted transcripts are written to S3 by the backend directly.

- **Migration:** One Alembic migration adding the `documents` table.

---

## 2. Proposed Solution & Implementation Plan

### 2.1 Data Model / Database Changes

**New enums** (Python `StrEnum`, stored as VARCHAR):

| Enum | Values |
|------|--------|
| `DocumentType` | `cv`, `transcript` |
| `DocumentStatus` | `pending`, `active` |
| `InterviewStage` | `screening`, `technical` |
| `InputMethod` | `file`, `paste` |

**New table:**

| Table | Column | Type | Constraints / Notes |
|-------|--------|------|---------------------|
| `documents` | `id` | INT | PK, autoincrement |
| | `type` | VARCHAR | Not null; `DocumentType` enum |
| | `candidate_position_id` | INT | FK → `candidate_positions.id`, not null |
| | `file_name` | VARCHAR | Original filename; null for pasted transcripts |
| | `s3_key` | VARCHAR | S3 object key; not null, unique |
| | `file_size` | BIGINT | Bytes; null for pasted transcripts |
| | `content_type` | VARCHAR | MIME type (e.g. `application/pdf`, `text/plain`) |
| | `status` | VARCHAR | `DocumentStatus` enum; default `pending` |
| | `interview_stage` | VARCHAR | `InterviewStage` enum; nullable (transcript-only) |
| | `interviewer_id` | INT | FK → `users.id`; nullable (transcript-only) |
| | `interview_date` | DATE | Nullable (transcript-only) |
| | `notes` | TEXT | Nullable (transcript-only) |
| | `input_method` | VARCHAR | `InputMethod` enum; nullable (transcript-only) |
| | `uploaded_by_id` | INT | FK → `users.id`, not null |
| | `created_at` | TIMESTAMP | `server_default=func.now()` |
| | `updated_at` | TIMESTAMP | `server_default=func.now()`, onupdate |

**Indexes:** `candidate_position_id`, `uploaded_by_id`, `interviewer_id` (FK indexes). Composite index on (`candidate_position_id`, `type`, `status`) for filtered list queries.

**CV versioning:** No explicit version column. "Current" CV = the most recently created `active` document with `type=cv` for a given `candidate_position_id`, ordered by `created_at DESC`. All older records are previous versions. This avoids race conditions and version numbering complexity.

**S3 key structure:** `documents/{uuid}/{original_filename}` — UUID ensures uniqueness, original filename preserved for display.

**Files:**
- `app/backend/app/models/document.py` — `Document` SQLModel
- Update `app/backend/app/models/enums.py` — add `DocumentType`, `DocumentStatus`, `InterviewStage`, `InputMethod`
- Update `app/backend/app/models/__init__.py` — import `Document`

**Migration:** Single Alembic migration `YYYY-MM-DD_add_documents_table.py`.

### 2.2 API Contracts

All endpoints require authentication (`get_current_user` dependency). New router: `app/backend/app/routers/documents.py`.

#### Documents Router

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/documents/presign` | Request presigned upload URL; creates a `pending` document record |
| `POST` | `/api/documents/{document_id}/complete` | Confirm upload succeeded; marks document `active` |
| `POST` | `/api/documents/paste` | Create pasted transcript (backend writes text to S3, record created as `active`) |
| `GET` | `/api/documents/{document_id}` | Get document detail with a presigned view URL |

#### Candidate Documents (nested under existing candidates router)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/candidates/{candidate_id}/documents` | List all documents for a candidate across positions |

**Request/response shapes:**

`POST /api/documents/presign`:
- Request: `{ type: "cv"|"transcript", candidate_position_id: int, file_name: str, content_type: str, file_size: int, interview_stage?: "screening"|"technical", interviewer_id?: int, interview_date?: "YYYY-MM-DD", notes?: str }`
- Response (201): `{ document_id: int, upload_url: str, s3_key: str }`
- Errors: 400 (file too large, invalid content type), 404 (candidate_position not found), 422 (missing transcript metadata)

`POST /api/documents/{document_id}/complete`:
- Response (200): `DocumentResponse`
- Errors: 404 (document not found), 409 (already completed or not owned by current user)

`POST /api/documents/paste`:
- Request: `{ candidate_position_id: int, content: str, interview_stage: "screening"|"technical", interviewer_id: int, interview_date: "YYYY-MM-DD", notes?: str }`
- Response (201): `DocumentResponse`
- Errors: 404 (candidate_position not found), 422 (missing required fields)

`GET /api/documents/{document_id}`:
- Response (200): `DocumentDetailResponse` (includes `view_url`: presigned GET URL, 60-min expiry)
- Errors: 404

`GET /api/candidates/{candidate_id}/documents`:
- Query params: `position_id?` (int), `type?` ("cv"|"transcript")
- Response (200): `DocumentResponse[]` ordered by `created_at DESC`

**`DocumentResponse` shape:** `{ id, type, candidate_position_id, file_name, s3_key, file_size, content_type, status, interview_stage, interviewer_id, interviewer_name, interview_date, notes, input_method, uploaded_by_id, uploaded_by_name, created_at, updated_at }`

**`DocumentDetailResponse`** extends `DocumentResponse` with `view_url: str`.

**Validation rules:**
- `file_size` ≤ 25 MB (26,214,400 bytes)
- `content_type` must be one of: `application/pdf`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`, `text/markdown`, `text/plain`
- For transcripts: DOCX is also allowed (in addition to PDF, TXT, MD)
- If `type=transcript`: `interview_stage`, `interviewer_id`, `interview_date` are required
- `uploaded_by_id` inferred from `current_user`

**Presigned URL expiration:** 15 minutes for upload URLs, 60 minutes for view URLs.

**Schemas:** `app/backend/app/schemas/documents.py`

### 2.3 Service Layer

| File | Key Functions |
|------|--------------|
| `app/backend/app/services/storage_service.py` | `generate_upload_url(s3_key, content_type, max_size)` → presigned PUT URL; `generate_view_url(s3_key, expiration)` → presigned GET URL; `put_text_object(s3_key, content, content_type)` → write text to S3; `delete_object(s3_key)` → cleanup |
| `app/backend/app/services/document_service.py` | `create_presigned_upload(session, type, candidate_position_id, file_name, content_type, file_size, uploaded_by_id, transcript_metadata?)` → `(Document, upload_url)`; `complete_upload(session, document_id, user_id)` → `Document`; `create_pasted_transcript(session, candidate_position_id, content, interview_stage, interviewer_id, interview_date, notes, uploaded_by_id)` → `Document`; `get_document(session, document_id)` → `dict | None` (includes view_url); `list_candidate_documents(session, candidate_id, position_id?, type?)` → `list[dict]` |

`storage_service.py` uses `aioboto3` for async S3 operations. AWS credentials resolved via standard chain (env vars / IAM role on ECS). Bucket name and region from `Settings`.

### 2.4 Configuration

New settings in `app/backend/app/config.py`:

| Setting | Type | Default | Notes |
|---------|------|---------|-------|
| `s3_bucket_name` | `str` | `""` | Required for file storage |
| `s3_region` | `str` | `"us-east-1"` | AWS region for S3 |

New dependency in `pyproject.toml`: `aioboto3`

Update `.env.example` with `S3_BUCKET_NAME` and `S3_REGION`.

### 2.5 Frontend: New Dependencies & Components

**Install:**
```bash
bun add mammoth react-markdown
bunx shadcn@latest add progress tooltip
```

**New feature module** (`src/features/documents/`):

| File | Export | Purpose |
|------|--------|---------|
| `hooks/use-documents.ts` | `useDocuments(candidateId, positionId?, type?)` | Query hook for document list |
| `hooks/use-presign-upload.ts` | `usePresignUpload()` | Mutation: request presigned URL |
| `hooks/use-complete-upload.ts` | `useCompleteUpload()` | Mutation: confirm upload |
| `hooks/use-paste-transcript.ts` | `usePasteTranscript()` | Mutation: create pasted transcript |
| `hooks/use-document.ts` | `useDocument(documentId)` | Query hook for single document + view URL |
| `index.ts` | Barrel exports | Public API |

**New widget components** (`src/widgets/documents/`):

| File | Purpose |
|------|---------|
| `upload-zone.tsx` | Drag-and-drop file input with format/size validation, multiple file support, per-file status display |
| `document-list.tsx` | Table of documents with type badge, filename/stage, date, uploader name. Groups by position when showing all candidate docs |
| `document-viewer.tsx` | Full-screen dialog viewer: PDF via `<embed>`/`<iframe>`, DOCX via mammoth.js → HTML, MD via react-markdown, TXT/pasted as `<pre>` plain text. Shows metadata header (filename, date, uploader, stage/interviewer for transcripts) |
| `cv-upload-dialog.tsx` | Dialog wrapping `upload-zone.tsx` for CV file upload. Shows version history link if CV already exists |
| `transcript-upload-dialog.tsx` | Tabbed dialog (File Upload / Paste Text) with metadata form: interview stage dropdown, interviewer dropdown (from users list), date picker, notes text field |
| `global-upload-menu.tsx` | "+" dropdown menu in app shell with "Upload CV" and "Upload Transcript" options. Each opens a dialog: candidate search/select → position select → upload form |

### 2.6 Frontend: Integration Points

**Candidate Detail page** (`src/routes/_authenticated/candidates/$candidateId.tsx`):
- Add a "Documents" Card section below the existing Positions section
- Per position: show "Upload CV" and "Add Transcript" actions
- CV display: current filename + date, or "Upload CV" if none. "Version history" link when versions exist
- Transcript list: grouped by stage (Screening, Technical), each entry shows interviewer, date, input method
- Clicking any document opens `document-viewer.tsx`

**App shell** (`src/routes/_authenticated.tsx` or `src/widgets/sidebar/sidebar.tsx`):
- Add "+" button (persistent, visible on all authenticated pages)
- Click opens `global-upload-menu.tsx` dropdown
- "Upload CV" flow: search/select candidate → select position → file upload
- "Upload Transcript" flow: search/select candidate → select position → transcript form

**Candidate/position selectors** in global upload menu reuse existing `GET /api/candidates?search=` and candidate detail data for position list. No new backend endpoints needed.

### 2.7 API Client Regeneration

After backend endpoints are built:
1. Start backend dev server → export OpenAPI JSON
2. Copy `openapi.json` to `app/frontend/`
3. Run `bun run generate:api` to regenerate typed client + TanStack Query hooks
4. Build feature hooks wrapping generated options

---

## 3. Impact and Risk Analysis

**System Dependencies:**
- New `documents` table depends on existing `candidate_positions` and `users` tables (FKs)
- S3 bucket must exist with proper CORS configuration for browser-direct uploads
- `aioboto3` adds an async AWS SDK dependency to the backend
- Frontend document viewer depends on `mammoth` (DOCX) and `react-markdown` (MD) — both are client-side only

**Risks & Mitigations:**

| Risk | Mitigation |
|------|-----------|
| Presigned URL expires before upload completes (slow connection) | 15-min expiry is generous for 25 MB; frontend catches S3 403 and re-requests presigned URL |
| Orphaned `pending` records (upload started but never confirmed) | Acceptable for POC; add periodic cleanup job later. List queries filter by `status=active` |
| S3 CORS misconfiguration blocks browser-direct uploads | Document required CORS config (`AllowedOrigins`, `AllowedMethods: PUT`, `AllowedHeaders: Content-Type`) in deployment/infra docs |
| DOCX rendering loses complex formatting (mammoth.js) | Acceptable for POC — CVs are primarily text content. PDF is the recommended format for best fidelity |
| Content type spoofing (user renames file extension) | Server-side validation of `content_type` against allowed list on `/presign`. S3 key includes original filename for auditability |
| Concurrent CV uploads for same candidate-position | Last to call `/complete` becomes "current" (latest `created_at`); no data loss since all versions are preserved |
| Large file uploads stall UI | Presigned URL uploads bypass backend entirely; frontend shows per-file progress via `XMLHttpRequest` upload events |

---

## 4. Testing Strategy

### 4.1 Backend Tests

- **Unit tests** for `document_service`: CV version ordering logic, transcript metadata requirement enforcement, validation rules (file size, content type), status transitions (pending → active)
- **Integration tests** per endpoint:
  - Presign happy path (CV + transcript), complete happy path, paste happy path
  - Validation errors: oversized file, invalid content type, missing transcript metadata, nonexistent candidate_position_id
  - List documents with filters (by position, by type)
  - Get document detail (includes view URL)
  - Auth: reject unauthenticated requests
- **S3 mocking:** Mock `storage_service` functions with `unittest.mock.patch` — no real S3 calls in tests. Focus on business logic and API contract.
- **File:** `tests/test_documents.py`

### 4.2 Browser Test Plan (Local E2E via Playwright)

**Prerequisites:** Both servers running locally. S3 bucket configured (or localstack). User logged in.

#### Scenario 1: Upload CV from Candidate Detail

| # | Action | Expected |
|---|--------|----------|
| 1.1 | Navigate to a candidate detail page with at least one position linked | Candidate detail loads, positions visible |
| 1.2 | Click "Upload CV" for a position | File picker dialog opens with drag-drop zone |
| 1.3 | Drop a PDF file (< 25 MB) | File appears in zone with name and size, valid status |
| 1.4 | Confirm upload | Progress shown, then success. CV filename + date displayed on position row |
| 1.5 | Click on the CV filename | Document viewer opens, PDF rendered in embed |
| 1.6 | Close viewer, upload a new CV (DOCX) for the same position | New file becomes current, previous remains in history |
| 1.7 | Click "Version history" | List of 2 versions shown with dates and uploader names |
| 1.8 | Click older version | Viewer opens showing the first PDF |

#### Scenario 2: Upload Transcript (File + Paste)

| # | Action | Expected |
|---|--------|----------|
| 2.1 | Click "Add Transcript" for a position | Transcript dialog opens with File/Paste tabs, metadata form |
| 2.2 | Select "File Upload" tab, drop a TXT file, fill stage=Screening, interviewer, date | Form populated |
| 2.3 | Submit | Transcript appears in list grouped under "Screening" |
| 2.4 | Click "Add Transcript" again, select "Paste Text" tab | Text area visible |
| 2.5 | Paste transcript text, fill stage=Technical, interviewer, date, notes | Form populated |
| 2.6 | Submit | Transcript appears under "Technical" group |
| 2.7 | Click the pasted transcript | Viewer shows plain text with metadata header |

#### Scenario 3: Validation & Error Cases

| # | Action | Expected |
|---|--------|----------|
| 3.1 | Try uploading an unsupported format (e.g. .jpg) | Error: "Unsupported file format. Please upload a PDF, DOCX, or MD file." |
| 3.2 | Try uploading a file > 25 MB | Error: "File is too large. Maximum size is 25 MB." |
| 3.3 | Try submitting transcript without required metadata | Form validation errors on stage, interviewer, date |

#### Scenario 4: Global Quick Action

| # | Action | Expected |
|---|--------|----------|
| 4.1 | Click "+" button in app header/sidebar | Menu shows "Upload CV" and "Upload Transcript" |
| 4.2 | Select "Upload CV" | Dialog: candidate search → select → position select → file upload |
| 4.3 | Search for a candidate by name, select, choose position, upload file | Success. Can navigate to candidate detail or dismiss |
| 4.4 | Select "Upload Transcript", go through same flow with transcript form | Success |

#### Scenario 5: Bulk Upload

| # | Action | Expected |
|---|--------|----------|
| 5.1 | In CV upload dialog, select 3 files (2 valid PDF, 1 invalid JPG) | Summary shows: 2 valid, 1 invalid with reason |
| 5.2 | Confirm upload | 2 files upload with progress, 1 flagged as failed. "2 of 3 files uploaded successfully." |
| 5.3 | Check version history | Both valid files appear as versions |

#### Scenario 6: Documents Section on Candidate Detail

| # | Action | Expected |
|---|--------|----------|
| 6.1 | Navigate to candidate with uploads from previous scenarios | Documents section shows all uploads across positions |
| 6.2 | Verify grouping by position | Each position has its CVs and transcripts listed |
| 6.3 | Navigate to a candidate with no documents | Empty state: "No documents uploaded yet. Upload a CV or transcript to get started." |
