"""add evaluation_instructions to positions

Revision ID: afb27e252a08
Revises: 666fd1a8412d
Create Date: 2026-03-11 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "afb27e252a08"
down_revision: str | Sequence[str] | None = "666fd1a8412d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("positions", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("evaluation_instructions", sa.Text(), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table("positions", schema=None) as batch_op:
        batch_op.drop_column("evaluation_instructions")
