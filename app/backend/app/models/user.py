from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, func
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(
        default=None,
        sa_column=Column(Integer, primary_key=True, autoincrement=True),
    )
    email: str = Field(
        sa_column=Column(String, unique=True, nullable=False, index=True)
    )
    google_id: str = Field(
        sa_column=Column(String, unique=True, nullable=False, index=True)
    )
    full_name: str = Field(sa_column=Column(String, nullable=False))
    avatar_url: str | None = Field(
        default=None, sa_column=Column(String, nullable=True)
    )
    created_at: datetime = Field(
        sa_column=Column(DateTime, nullable=False, server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
        )
    )
