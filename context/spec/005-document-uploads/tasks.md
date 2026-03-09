# Tasks: Document Uploads (CV & Transcript)

- **Spec:** `context/spec/005-document-uploads/`
- **Status:** Complete

---

## Slice 1: Backend — Document model, S3 storage, presigned upload + confirm

After completion, the API accepts presign requests and confirms uploads. Testable via pytest.

- [x] **1.1** Add `DocumentType`, `DocumentStatus`, `InterviewStage`, `InputMethod` enums to `app/backend/app/models/enums.py` **[Agent: python-architect]**
- [x] **1.2** Create `Document` SQLModel in `app/backend/app/models/document.py` with all columns per tech spec (type, candidate_position_id, s3_key, file_name, file_size, content_type, status, transcript-specific nullable fields, uploaded_by_id, timestamps). Add composite index on (`candidate_position_id`, `type`, `status`) **[Agent: python-architect]**
- [x] **1.3** Update `app/backend/app/models/__init__.py` to import `Document` **[Agent: python-architect]**
- [x] **1.4** Add `s3_bucket_name` and `s3_region` to `Settings` in `config.py`; update `.env.example` with `S3_BUCKET_NAME` and `S3_REGION` **[Agent: python-architect]**
- [x] **1.5** Add `aioboto3` dependency to `pyproject.toml` **[Agent: python-architect]**
- [x] **1.6** Create `app/backend/app/services/storage_service.py` — async S3 operations: `generate_upload_url(s3_key, content_type, max_size)`, `generate_view_url(s3_key, expiration)`, `put_text_object(s3_key, content, content_type)`, `delete_object(s3_key)` **[Agent: python-architect]**
- [x] **1.7** Create `app/backend/app/schemas/documents.py` — Pydantic request/response models: `PresignRequest`, `PresignResponse`, `PasteTranscriptRequest`, `DocumentResponse`, `DocumentDetailResponse` **[Agent: python-architect]**
- [x] **1.8** Create `app/backend/app/services/document_service.py` — `create_presigned_upload(session, ...)` and `complete_upload(session, document_id, user_id)` **[Agent: python-architect]**
- [x] **1.9** Create `app/backend/app/routers/documents.py` with `POST /api/documents/presign` and `POST /api/documents/{document_id}/complete`; register router in `main.py` **[Agent: python-architect]**
- [x] **1.10** Create Alembic migration `YYYY-MM-DD_add_documents_table.py` **[Agent: python-architect]**
- [x] **1.11** Write backend tests in `tests/test_documents.py`: presign happy path (CV + transcript), complete happy path, validation errors (oversize file, bad content type, missing transcript metadata, nonexistent candidate_position_id, already-completed document). Mock `storage_service` with `unittest.mock.patch`. **[Agent: python-architect]**
- [x] **1.12** **Verify:** Run `uv run pytest tests/test_documents.py` — all tests pass. Run `uv run ruff check .` — no lint errors. **[Agent: python-architect]**

---

## Slice 2: Backend — Paste transcript, list documents, document detail

Completes all backend endpoints. After completion, the full document API is functional.

- [x] **2.1** Add `create_pasted_transcript`, `get_document`, `list_candidate_documents` to `document_service.py` **[Agent: python-architect]**
- [x] **2.2** Add `POST /api/documents/paste` endpoint — writes text to S3 via `storage_service.put_text_object`, creates active document record **[Agent: python-architect]**
- [x] **2.3** Add `GET /api/documents/{document_id}` endpoint — returns `DocumentDetailResponse` with presigned view URL (60-min expiry) **[Agent: python-architect]**
- [x] **2.4** Add `GET /api/candidates/{candidate_id}/documents` endpoint with `position_id` and `type` query params — returns `DocumentResponse[]` ordered by `created_at DESC` **[Agent: python-architect]**
- [x] **2.5** Write backend tests: paste happy path + validation errors (missing metadata, empty content), list by candidate, list with `position_id` filter, list with `type` filter, get document detail with view URL, 404 for nonexistent document **[Agent: python-architect]**
- [x] **2.6** **Verify:** Run `uv run pytest` (full suite) — all tests pass. Run `uv run ruff check .` — clean. **[Agent: python-architect]**

---

## Slice 3: Frontend — CV upload from candidate detail page

First frontend slice. Users can upload a CV and see it listed on the candidate detail page.

- [x] **3.1** Regenerate API client: start backend dev server, export OpenAPI spec to `app/frontend/openapi.json`, run `bun run generate:api` **[Agent: react-architect]**
- [x] **3.2** Install new shadcn/ui components: `bunx shadcn@latest add progress tooltip` **[Agent: react-architect]**
- [x] **3.3** Create `src/features/documents/` module with hooks: `usePresignUpload`, `useCompleteUpload`, `useDocuments`, and barrel `index.ts` **[Agent: react-architect]**
- [x] **3.4** Create `src/widgets/documents/upload-zone.tsx` — drag-and-drop file input with format validation (PDF, DOCX, MD for CVs), size validation (25 MB), progress indicator via `XMLHttpRequest` upload events to S3 presigned URL **[Agent: react-architect]**
- [x] **3.5** Create `src/widgets/documents/cv-upload-dialog.tsx` — dialog wrapping upload zone; orchestrates presign → S3 upload → complete flow **[Agent: react-architect]**
- [x] **3.6** Create `src/widgets/documents/document-list.tsx` — table showing documents with type badge, filename, upload date, uploader name **[Agent: react-architect]**
- [x] **3.7** Integrate into `$candidateId.tsx`: add "Upload CV" action per position row; show document list section below positions **[Agent: react-architect]**
- [x] **3.8** **Verify via Playwright:** Navigate to candidate with linked position → click "Upload CV" → drop a PDF → confirm upload → CV filename and date appear in list. Try .jpg → error: "Unsupported file format." **[Agent: react-architect]**

---

## Slice 4: Frontend — In-app document viewer + CV version history

Users can view documents in-app and navigate CV version history.

- [x] **4.1** Install viewer dependencies: `bun add mammoth react-markdown` **[Agent: react-architect]**
- [x] **4.2** Create `src/features/documents/hooks/use-document.ts` hook — fetch document detail with presigned view URL **[Agent: react-architect]**
- [x] **4.3** Create `src/widgets/documents/document-viewer.tsx` — full-screen dialog: PDF via `<embed>`/`<iframe>`, DOCX via mammoth.js→HTML, MD via react-markdown, TXT/plain as `<pre>`. Metadata header: filename, upload date, uploader name **[Agent: react-architect]**
- [x] **4.4** Wire viewer: click any document in `document-list.tsx` → opens viewer dialog **[Agent: react-architect]**
- [x] **4.5** Extend `document-list.tsx`: mark latest CV as "Current" badge, show "Version history" link when multiple CVs exist for a candidate-position **[Agent: react-architect]**
- [x] **4.6** Create version history popover/dialog: all CV versions ordered newest-first, each clickable to open viewer **[Agent: react-architect]**
- [x] **4.7** **Verify via Playwright:** Upload 2 CVs for same position (PDF then DOCX) → latest shows "Current" → click it → DOCX renders as HTML → open version history → both versions listed → click older PDF → renders in embed. Close viewer → returns to page. **[Agent: react-architect]**

---

## Slice 5: Frontend — Transcript upload (file + paste) with metadata

Users can upload transcript files and paste transcript text with interview metadata.

- [x] **5.1** Create `src/features/documents/hooks/use-paste-transcript.ts` hook **[Agent: react-architect]**
- [x] **5.2** Create `src/widgets/documents/transcript-upload-dialog.tsx` — tabbed dialog (File Upload / Paste Text) with metadata form: interview stage dropdown (Screening/Technical), interviewer dropdown (from `GET /api/users`), date picker, optional notes field **[Agent: react-architect]**
- [x] **5.3** Extend `document-list.tsx`: display transcripts grouped by stage (Screening, Technical); each entry shows interviewer name, interview date, upload date, input method (file/paste); ordered by interview date within each group **[Agent: react-architect]**
- [x] **5.4** Add "Add Transcript" action per position on candidate detail page, wired to transcript dialog **[Agent: react-architect]**
- [x] **5.5** **Verify via Playwright:** Click "Add Transcript" → File tab → drop TXT, Screening stage, pick interviewer, set date → submit → appears under "Screening". Add another → Paste tab → paste text, Technical stage, fill metadata + notes → submit → appears under "Technical". Click pasted transcript → viewer shows plain text with metadata. **[Agent: react-architect]**

---

## Slice 6: Frontend — Documents section (aggregate view) on candidate detail

Dedicated Documents section showing all uploads across all positions.

- [x] **6.1** Add "Documents" Card section to `$candidateId.tsx`, below Positions section **[Agent: react-architect]**
- [x] **6.2** Display all documents grouped by position: type label (CV/Transcript), filename/stage, date, uploader. Each clickable to open viewer **[Agent: react-architect]**
- [x] **6.3** Empty state: "No documents uploaded yet. Upload a CV or transcript to get started." **[Agent: react-architect]**
- [x] **6.4** **Verify via Playwright:** Navigate to candidate with uploads → Documents section shows all docs grouped by position. Navigate to candidate with no documents → empty state message shown. **[Agent: react-architect]**

---

## Slice 7: Frontend — Global quick action ("+" button)

Users can upload CVs and transcripts from any page via a persistent "+" button.

- [x] **7.1** Create `src/widgets/documents/global-upload-menu.tsx` — dropdown with "Upload CV" and "Upload Transcript" **[Agent: react-architect]**
- [x] **7.2** Add candidate search/select step with typeahead (reuses `GET /api/candidates?search=`) **[Agent: react-architect]**
- [x] **7.3** Add position select step (fetches candidate's positions after selection) **[Agent: react-architect]**
- [x] **7.4** Wire: after candidate+position selected → open CV upload dialog or transcript dialog **[Agent: react-architect]**
- [x] **7.5** Add "+" button to authenticated layout (`_authenticated.tsx` or sidebar), visible on all pages **[Agent: react-architect]**
- [x] **7.6** After successful upload: option to navigate to candidate detail or dismiss **[Agent: react-architect]**
- [x] **7.7** **Verify via Playwright:** From dashboard → click "+" → "Upload CV" → search candidate by name → select → pick position → upload PDF → success with navigation option. Repeat with "Upload Transcript" flow including metadata. **[Agent: react-architect]**

---

## Slice 8: Bulk upload support

Users can select or drag-drop multiple files at once in any upload dialog.

- [x] **8.1** Extend `upload-zone.tsx` to accept multiple files; validate each independently (format, size); show per-file status (valid/invalid with reason) **[Agent: react-architect]**
- [x] **8.2** Add pre-upload summary: list of files with validation status. Invalid flagged, valid ready **[Agent: react-architect]**
- [x] **8.3** Implement parallel presign → S3 upload → complete flow per valid file, with per-file progress indicators **[Agent: react-architect]**
- [x] **8.4** Show completion summary: "N of M files uploaded successfully. Failed: [filenames with reasons]." **[Agent: react-architect]**
- [x] **8.5** CV bulk: each file becomes a separate version (last file in batch = current) **[Agent: react-architect]**
- [x] **8.6** Transcript bulk: each file creates a separate transcript entry, all sharing same metadata from form **[Agent: react-architect]**
- [x] **8.7** **Verify via Playwright:** CV upload → drop 3 files (2 valid PDFs, 1 invalid JPG) → summary shows 2 valid, 1 invalid → confirm → per-file progress → "2 of 3 files uploaded successfully" → version history shows both valid files. **[Agent: react-architect]**
