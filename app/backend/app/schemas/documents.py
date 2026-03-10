from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.enums import DocumentType, InterviewStage

VALID_INTERVIEW_STAGES = {s.value for s in InterviewStage}


def _normalize_interview_stage(v: str) -> str:
    normalized = v.lower()
    if normalized not in VALID_INTERVIEW_STAGES:
        valid_stages = ", ".join(sorted(VALID_INTERVIEW_STAGES))
        msg = f"interview_stage must be one of: {valid_stages}"
        raise ValueError(msg)
    return normalized


ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/markdown",
    "text/plain",
}

MAX_FILE_SIZE = 26_214_400


class PresignRequest(BaseModel):
    type: str
    candidate_position_id: int
    file_name: str
    content_type: str
    file_size: int
    interview_stage: str | None = None
    interviewer_id: int | None = None
    interview_date: date | None = None
    notes: str | None = None

    @field_validator("interview_stage", mode="before")
    @classmethod
    def validate_interview_stage(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return _normalize_interview_stage(v)

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        valid_types = {t.value for t in DocumentType}
        if v not in valid_types:
            msg = f"Document type must be one of: {', '.join(sorted(valid_types))}"
            raise ValueError(msg)
        return v

    @field_validator("file_size")
    @classmethod
    def validate_file_size(cls, v: int) -> int:
        if v > MAX_FILE_SIZE:
            msg = f"File size must not exceed {MAX_FILE_SIZE} bytes (25 MB)"
            raise ValueError(msg)
        return v

    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, v: str) -> str:
        if v not in ALLOWED_CONTENT_TYPES:
            msg = f"Content type must be one of: {', '.join(ALLOWED_CONTENT_TYPES)}"
            raise ValueError(msg)
        return v

    @model_validator(mode="after")
    def validate_transcript_metadata(self) -> "PresignRequest":
        if self.type == "transcript":
            missing_fields = []
            if self.interview_stage is None:
                missing_fields.append("interview_stage")
            if self.interviewer_id is None:
                missing_fields.append("interviewer_id")
            if self.interview_date is None:
                missing_fields.append("interview_date")

            if missing_fields:
                msg = (
                    f"For transcript documents, the following fields are required: "
                    f"{', '.join(missing_fields)}"
                )
                raise ValueError(msg)

        return self


class PresignResponse(BaseModel):
    document_id: int
    upload_url: str
    s3_key: str


class PasteTranscriptRequest(BaseModel):
    candidate_position_id: int
    content: str = Field(min_length=1)
    interview_stage: str
    interviewer_id: int
    interview_date: date
    notes: str | None = None

    @field_validator("interview_stage", mode="before")
    @classmethod
    def validate_interview_stage(cls, v: str) -> str:
        return _normalize_interview_stage(v)


class DocumentResponse(BaseModel):
    id: int
    type: str
    candidate_position_id: int
    file_name: str | None
    file_size: int | None
    content_type: str
    status: str
    interview_stage: str | None
    interviewer_id: int | None
    interviewer_name: str | None
    interview_date: date | None
    notes: str | None
    input_method: str | None
    uploaded_by_id: int
    uploaded_by_name: str | None
    created_at: datetime
    updated_at: datetime


class DocumentDetailResponse(DocumentResponse):
    view_url: str
