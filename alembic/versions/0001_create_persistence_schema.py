"""create persistence schema

Revision ID: 0001_create_persistence_schema
Revises: 
Create Date: 2026-05-29 00:00:00.000000
"""

from __future__ import annotations

from alembic import op

from app.src.config.database import Base
from app.src.models import user as user_models  # noqa: F401
from app.src.models import persistence as persistence_models  # noqa: F401

# revision identifiers, used by Alembic.
revision = "0001_create_persistence_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
