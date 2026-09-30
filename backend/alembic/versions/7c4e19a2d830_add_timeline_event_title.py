"""Add an independent title to timeline events.

Revision ID: 7c4e19a2d830
Revises: 1b6558707e9e
"""
from alembic import op
import sqlalchemy as sa

revision = "7c4e19a2d830"
down_revision = "1b6558707e9e"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("timeline_events", sa.Column("title", sa.String(120), nullable=False, server_default=""))


def downgrade():
    op.drop_column("timeline_events", "title")
