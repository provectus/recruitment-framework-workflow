from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, func
from sqlmodel import Field, SQLModel


class Candidate(SQLModel, table=True):
    __tablename__ = "candidates"

    id: int | None = Field(
        default=None, sa_column=Column(Integer, primary_key=True, autoincrement=True)
    )
    full_name: str = Field(sa_column=Column(String, nullable=False))
    email: str = Field(
        sa_column=Column(String, unique=True, nullable=False, index=True)
    )
    is_archived: bool = Field(default=False, sa_column=Column(Boolean, nullable=False))
    created_at: datetime = Field(
        sa_column=Column(DateTime, nullable=False, server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
        )
    )
