from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, func
from sqlmodel import Field, SQLModel


class Team(SQLModel, table=True):
    __tablename__ = "teams"

    id: int | None = Field(
        default=None, sa_column=Column(Integer, primary_key=True, autoincrement=True)
    )
    name: str = Field(sa_column=Column(String, unique=True, nullable=False))
    is_archived: bool = Field(default=False, sa_column=Column(Boolean, nullable=False))
    created_at: datetime = Field(
        sa_column=Column(DateTime, nullable=False, server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
        )
    )
