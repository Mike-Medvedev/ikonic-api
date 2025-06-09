"""remove character limit from mountain.

Revision ID: 59b0936ff419
Revises: ac817b4a2bf5
Create Date: 2025-06-09 00:35:48.934153

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '59b0936ff419'
down_revision: str | None = 'ac817b4a2bf5'
branch_labels: str | list[str] | None = None
depends_on: str | list[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "trips",                
        "mountain",
        existing_type=sa.String(length=50),
        type_=sa.Text(),                  # Converts from VARCHAR(50) → TEXT
        existing_nullable=False,
    )
   


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "trips",
        "mountain",
        existing_type=sa.Text(),
        type_=sa.String(length=50),
        existing_nullable=False,
    )