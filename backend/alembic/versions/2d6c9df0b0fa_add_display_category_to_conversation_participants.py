"""add display category to conversation participants

Revision ID: 2d6c9df0b0fa
Revises: 5a8dd0b1c3c2
Create Date: 2026-04-24 20:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "2d6c9df0b0fa"
down_revision = "5a8dd0b1c3c2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("conversation_participants") as batch_op:
        batch_op.add_column(
            sa.Column(
                "display_category",
                sa.Enum("PRIVATE", "WORK", "OTHER", name="conversationdisplaycategoryenum"),
                nullable=False,
                server_default="OTHER",
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("conversation_participants") as batch_op:
        batch_op.drop_column("display_category")
