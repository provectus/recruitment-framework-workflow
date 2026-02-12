import enum


class PositionStatus(str, enum.Enum):
    open = "open"
    on_hold = "on_hold"
    closed = "closed"


class PipelineStage(str, enum.Enum):
    new = "new"
    screening = "screening"
    technical = "technical"
    offer = "offer"
    hired = "hired"
    rejected = "rejected"
