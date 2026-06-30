"""Add Google Auth

Revision ID: 8486516615a7
Revises: 089b49d0b1f0
Create Date: 2026-06-30 18:49:16.658063

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8486516615a7'
down_revision: Union[str, None] = '089b49d0b1f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('auth_provider', sa.String(), server_default='password', nullable=False))
    op.add_column('users', sa.Column('google_id', sa.String(), nullable=True))
    op.alter_column('users', 'password_hash',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.create_unique_constraint(None, 'users', ['google_id'])


def downgrade() -> None:
    op.drop_constraint(None, 'users', type_='unique')
    op.alter_column('users', 'password_hash',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.drop_column('users', 'google_id')
    op.drop_column('users', 'auth_provider')
    # ### end Alembic commands ###
