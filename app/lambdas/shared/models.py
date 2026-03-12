"""
Lambda-local DB model definitions.

These models intentionally duplicate app/backend/app/models/ to keep Lambda
packages fully self-contained and independently deployable. The backend models
are the canonical source of truth — any schema change there must be mirrored
here manually.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
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


class CandidatePosition(SQLModel, table=True):
    __tablename__ = "candidate_positions"
    __table_args__ = (UniqueConstraint("candidate_id", "position_id"),)

    id: int | None = Field(
        default=None,
        sa_column=Column(Integer, primary_key=True, autoincrement=True),
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


class Position(SQLModel, table=True):
    __tablename__ = "positions"

    id: int | None = Field(
        default=None,
        sa_column=Column(Integer, primary_key=True, autoincrement=True),
    )
    title: str = Field(sa_column=Column(String, nullable=False))
    requirements: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    evaluation_instructions: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    status: str = Field(default="open", sa_column=Column(String, nullable=False))
    team_id: int = Field(
        sa_column=Column(Integer, ForeignKey("teams.id"), nullable=False)
    )
    hiring_manager_id: int = Field(
        sa_column=Column(Integer, ForeignKey("users.id"), nullable=False)
    )
    is_archived: bool = Field(
        default=False, sa_column=Column(Boolean, nullable=False)
    )
    created_at: datetime = Field(
        sa_column=Column(DateTime, nullable=False, server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
        )
    )


class Document(SQLModel, table=True):
    __tablename__ = "documents"
    __table_args__ = (
        Index(
            "ix_lambda_documents_candidate_position_type_status",
            "candidate_position_id",
            "type",
            "status",
        ),
    )

    id: int | None = Field(
        default=None,
        sa_column=Column(Integer, primary_key=True, autoincrement=True),
    )
    type: str = Field(sa_column=Column(String, nullable=False))
    candidate_position_id: int = Field(
        sa_column=Column(
            Integer, ForeignKey("candidate_positions.id"), nullable=False, index=True
        )
    )
    file_name: str | None = Field(
        default=None, sa_column=Column(String, nullable=True)
    )
    s3_key: str = Field(sa_column=Column(String, unique=True, nullable=False))
    status: str = Field(default="pending", sa_column=Column(String, nullable=False))
    created_at: datetime = Field(
        sa_column=Column(DateTime, nullable=False, server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
        )
    )


class PositionRubricVersion(SQLModel, table=True):
    __tablename__ = "position_rubric_versions"
    __table_args__ = (UniqueConstraint("position_rubric_id", "version_number"),)

    id: int | None = Field(
        default=None,
        sa_column=Column(Integer, primary_key=True, autoincrement=True),
    )
    position_rubric_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("position_rubrics.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    version_number: int = Field(sa_column=Column(Integer, nullable=False))
    structure: dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))
    created_by_id: int = Field(
        sa_column=Column(Integer, ForeignKey("users.id"), nullable=False)
    )
    created_at: datetime = Field(
        sa_column=Column(DateTime, nullable=False, server_default=func.now())
    )


class Evaluation(SQLModel, table=True):
    __tablename__ = "evaluations"
    __table_args__ = (
        UniqueConstraint("candidate_position_id", "step_type", "version"),
        Index(
            "ix_lambda_evaluations_candidate_position_status",
            "candidate_position_id",
            "status",
        ),
    )

    id: int | None = Field(
        default=None,
        sa_column=Column(Integer, primary_key=True, autoincrement=True),
    )
    candidate_position_id: int = Field(
        sa_column=Column(
            Integer, ForeignKey("candidate_positions.id"), nullable=False, index=True
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
