"""Create the HackEval relational schema.

Revision ID: 001_create_relational_schema
Revises:
"""

from alembic import op

from app.database import Base

revision = "001_create_relational_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(op.get_bind())
