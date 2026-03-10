import enum


class PositionStatus(enum.StrEnum):
    open = "open"
    on_hold = "on_hold"
    closed = "closed"


class PipelineStage(enum.StrEnum):
    new = "new"
    screening = "screening"
    technical = "technical"
    offer = "offer"
    hired = "hired"
    rejected = "rejected"


class DocumentType(enum.StrEnum):
    cv = "cv"
    transcript = "transcript"


class DocumentStatus(enum.StrEnum):
    pending = "pending"
    active = "active"


class InterviewStage(enum.StrEnum):
    screening = "screening"
    technical = "technical"


class InputMethod(enum.StrEnum):
    file = "file"
    paste = "paste"


class EvaluationStepType(enum.StrEnum):
    cv_analysis = "cv_analysis"
    screening_eval = "screening_eval"
    technical_eval = "technical_eval"
    recommendation = "recommendation"
    feedback_gen = "feedback_gen"


class EvaluationStatus(enum.StrEnum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
