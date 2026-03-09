"""add_documents_table

Revision ID: 8cab1f3271ca
Revises: 8127b1dec6d2
Create Date: 2026-02-13 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "8cab1f3271ca"
down_revision: str | Sequence[str] | None = "8127b1dec6d2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("candidate_position_id", sa.Integer(), nullable=False),
        sa.Column("file_name", sa.String(), nullable=True),
        sa.Column("s3_key", sa.String(), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=True),
        sa.Column("content_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("interview_stage", sa.String(), nullable=True),
        sa.Column("interviewer_id", sa.Integer(), nullable=True),
        sa.Column("interview_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("input_method", sa.String(), nullable=True),
        sa.Column("uploaded_by_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["candidate_position_id"],
            ["candidate_positions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["interviewer_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["uploaded_by_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("s3_key"),
    )
    with op.batch_alter_table("documents", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_documents_candidate_position_id"),
            ["candidate_position_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_documents_interviewer_id"),
            ["interviewer_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_documents_uploaded_by_id"),
            ["uploaded_by_id"],
            unique=False,
        )
        batch_op.create_index(
            "ix_documents_candidate_position_type_status",
            ["candidate_position_id", "type", "status"],
            unique=False,
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("documents", schema=None) as batch_op:
        batch_op.drop_index("ix_documents_candidate_position_type_status")
        batch_op.drop_index(batch_op.f("ix_documents_uploaded_by_id"))
        batch_op.drop_index(batch_op.f("ix_documents_interviewer_id"))
        batch_op.drop_index(batch_op.f("ix_documents_candidate_position_id"))

    op.drop_table("documents")
