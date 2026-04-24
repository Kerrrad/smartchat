"""add related conversation id to notifications

Revision ID: 5a8dd0b1c3c2
Revises: bef0fe2e844c
Create Date: 2026-04-18 22:10:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "5a8dd0b1c3c2"
down_revision = "bef0fe2e844c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("notifications") as batch_op:
        batch_op.add_column(sa.Column("related_conversation_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_notifications_related_conversation_id_conversations",
            "conversations",
            ["related_conversation_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    with op.batch_alter_table("notifications") as batch_op:
        batch_op.drop_constraint("fk_notifications_related_conversation_id_conversations", type_="foreignkey")
        batch_op.drop_column("related_conversation_id")
