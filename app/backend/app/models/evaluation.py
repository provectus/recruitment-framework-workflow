from datetime import datetime
from typing import Any

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.types import JSON
from sqlmodel import Field, SQLModel


class Evaluation(SQLModel, table=True):
    __tablename__ = "evaluations"
    __table_args__ = (
        UniqueConstraint("candidate_position_id", "step_type", "version"),
        Index(
            "ix_evaluations_candidate_position_status",
            "candidate_position_id",
            "status",
        ),
    )

    id: int | None = Field(
        default=None, sa_column=Column(Integer, primary_key=True, autoincrement=True)
    )
    candidate_position_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("candidate_positions.id"),
            nullable=False,
            index=True,
        )
    )
    step_type: str = Field(sa_column=Column(String, nullable=False))
    status: str = Field(default="pending", sa_column=Column(String, nullable=False))
    version: int = Field(default=1, sa_column=Column(Integer, nullable=False))
    source_document_id: int | None = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("documents.id"), nullable=True),
    )
    rubric_version_id: int | None = Field(
        default=None,
        sa_column=Column(
            Integer, ForeignKey("position_rubric_versions.id"), nullable=True
        ),
    )
    result: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )
    error_message: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    execution_arn: str | None = Field(
        default=None, sa_column=Column(String, nullable=True)
    )
    started_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime, nullable=True)
    )
    completed_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime, nullable=True)
    )
    created_at: datetime = Field(
        sa_column=Column(DateTime, nullable=False, server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
        )
    )
