"""adding unique constraints to invitations.

Revision ID: a777ccc563e7
Revises: 5b89e14261dc
Create Date: 2025-06-08 01:29:15.613054

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'a777ccc563e7'
down_revision: str | None = '5b89e14261dc'
branch_labels: str | list[str] | None = None
depends_on: str | list[str] | None = None


def upgrade() -> None:
    # Create partial unique indexes instead of constraints with WHERE clauses
    op.create_index(
        'unique_invitation_registered_user',
        'invitations',
        ['trip_id', 'user_id'],
        unique=True,
        postgresql_where=sa.text('user_id IS NOT NULL')
    )
    
    op.create_index(
        'unique_invitation_external_user',
        'invitations',
        ['trip_id', 'registered_phone'],
        unique=True,
        postgresql_where=sa.text('registered_phone IS NOT NULL')
    )

def downgrade() -> None:
    op.drop_index('unique_invitation_registered_user', 'invitations')
    op.drop_index('unique_invitation_external_user', 'invitations')