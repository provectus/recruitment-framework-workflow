from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlmodel import Field, SQLModel


class Document(SQLModel, table=True):
    __tablename__ = "documents"
    __table_args__ = (
        Index(
            "ix_documents_candidate_position_type_status",
            "candidate_position_id",
            "type",
            "status",
        ),
    )

    id: int | None = Field(
        default=None, sa_column=Column(Integer, primary_key=True, autoincrement=True)
    )
    type: str = Field(sa_column=Column(String, nullable=False))
    candidate_position_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("candidate_positions.id"),
            nullable=False,
            index=True,
        )
    )
    file_name: str | None = Field(default=None, sa_column=Column(String, nullable=True))
    s3_key: str = Field(sa_column=Column(String, unique=True, nullable=False))
    file_size: int | None = Field(
        default=None, sa_column=Column(BigInteger, nullable=True)
    )
    content_type: str = Field(sa_column=Column(String, nullable=False))
    status: str = Field(default="pending", sa_column=Column(String, nullable=False))
    interview_stage: str | None = Field(
        default=None, sa_column=Column(String, nullable=True)
    )
    interviewer_id: int | None = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("users.id"), nullable=True, index=True),
    )
    interview_date: date | None = Field(
        default=None, sa_column=Column(Date, nullable=True)
    )
    notes: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    input_method: str | None = Field(
        default=None, sa_column=Column(String, nullable=True)
    )
    uploaded_by_id: int = Field(
        sa_column=Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    )
    created_at: datetime = Field(
        sa_column=Column(DateTime, nullable=False, server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
        )
    )
