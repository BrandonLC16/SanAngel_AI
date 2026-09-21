"""Create the initial schema baseline.

Revision ID: 20260921_0001
Revises: None
Create Date: 2026-09-21
"""

from collections.abc import Sequence

revision: str = "20260921_0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Establish the migration baseline without creating future domain tables."""


def downgrade() -> None:
    """Return to the state before the migration baseline."""
