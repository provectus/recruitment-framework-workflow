from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.types import JSON
from sqlmodel import Field, SQLModel


class PositionRubric(SQLModel, table=True):
    __tablename__ = "position_rubrics"

    id: int | None = Field(
        default=None, sa_column=Column(Integer, primary_key=True, autoincrement=True)
    )
    position_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("positions.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        )
    )
    source_template_id: int | None = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("rubric_templates.id"), nullable=True),
    )
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
        default=None, sa_column=Column(Integer, primary_key=True, autoincrement=True)
    )
    position_rubric_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("position_rubrics.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    version_number: int = Field(sa_column=Column(Integer, nullable=False))
    structure: dict = Field(sa_column=Column(JSON, nullable=False))
    created_by_id: int = Field(
        sa_column=Column(Integer, ForeignKey("users.id"), nullable=False)
    )
    created_at: datetime = Field(
        sa_column=Column(DateTime, nullable=False, server_default=func.now())
    )
