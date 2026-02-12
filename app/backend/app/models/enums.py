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
