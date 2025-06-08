"""Initial baseline - database already exists.

Revision ID: 5b89e14261dc
Revises: 
Create Date: 2025-06-08 00:51:22.937489

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '5b89e14261dc'
down_revision: str | None = None
branch_labels: str | list[str] | None = None
depends_on: str | list[str] | None = None


def upgrade() -> None:
    """Database already exists - this is just a baseline."""
    pass

def downgrade() -> None:
    """Nothing to downgrade."""
    pass