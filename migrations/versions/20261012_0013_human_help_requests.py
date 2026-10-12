"""Persist a minimal pending human-help signal on responder state.

Revision ID: 20261012_0013
Revises: 20260925_0012
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261012_0013"
down_revision: str | Sequence[str] | None = "20260925_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("conversation_responder_states", sa.Column("help_reason", sa.String(32)))
    op.add_column("conversation_responder_states", sa.Column("help_requested_at", sa.DateTime()))


def downgrade() -> None:
    op.drop_column("conversation_responder_states", "help_requested_at")
    op.drop_column("conversation_responder_states", "help_reason")
