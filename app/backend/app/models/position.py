from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlmodel import Field, SQLModel


class Position(SQLModel, table=True):
    __tablename__ = "positions"

    id: int | None = Field(
        default=None, sa_column=Column(Integer, primary_key=True, autoincrement=True)
    )
    title: str = Field(sa_column=Column(String, nullable=False))
    requirements: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    status: str = Field(default="open", sa_column=Column(String, nullable=False))
    team_id: int = Field(
        sa_column=Column(Integer, ForeignKey("teams.id"), nullable=False)
    )
    hiring_manager_id: int = Field(
        sa_column=Column(Integer, ForeignKey("users.id"), nullable=False)
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
