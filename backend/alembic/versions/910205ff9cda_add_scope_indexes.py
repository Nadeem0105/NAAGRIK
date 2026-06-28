"""add_scope_indexes

Revision ID: 910205ff9cda
Revises: 1fae126e424f
Create Date: 2026-06-28

Adds indexes for the three columns that every admin request now
filters through:
  - regions.parent_region_id  (state-admin subquery)
  - issues.region_id          (scope filter on every admin issue fetch)
  - users.region_id           (scope lookup on login / assign-region)
"""
from alembic import op

# revision identifiers
revision = '910205ff9cda'
down_revision = '1fae126e424f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        'idx_regions_parent',
        'regions',
        ['parent_region_id'],
        unique=False
    )
    op.create_index(
        'idx_issues_region',
        'issues',
        ['region_id'],
        unique=False
    )
    op.create_index(
        'idx_users_region',
        'users',
        ['region_id'],
        unique=False
    )


def downgrade() -> None:
    op.drop_index('idx_users_region', table_name='users')
    op.drop_index('idx_issues_region', table_name='issues')
    op.drop_index('idx_regions_parent', table_name='regions')
