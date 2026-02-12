from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlmodel import Field, SQLModel


class CandidatePosition(SQLModel, table=True):
    __tablename__ = "candidate_positions"
    __table_args__ = (UniqueConstraint("candidate_id", "position_id"),)

    id: int | None = Field(
        default=None, sa_column=Column(Integer, primary_key=True, autoincrement=True)
    )
    candidate_id: int = Field(
        sa_column=Column(Integer, ForeignKey("candidates.id"), nullable=False)
    )
    position_id: int = Field(
        sa_column=Column(Integer, ForeignKey("positions.id"), nullable=False)
    )
    stage: str = Field(default="new", sa_column=Column(String, nullable=False))
    created_at: datetime = Field(
        sa_column=Column(DateTime, nullable=False, server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
        )
    )
