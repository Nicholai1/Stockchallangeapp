"""Add avg_cost column to user_portfolios

Revision ID: b1a2c3d4e5f6
Revises: 7fc4621bc253
Create Date: 2025-10-30 22:45:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b1a2c3d4e5f6'
down_revision = '7fc4621bc253'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add avg_cost column with a default of 0.0 to avoid nulls for existing rows
    op.add_column('user_portfolios', sa.Column('avg_cost', sa.Float(), nullable=False, server_default=sa.text('0.0')))
    # Remove server default now that rows are populated
    with op.get_context().autocommit_block():
        op.alter_column('user_portfolios', 'avg_cost', server_default=None)


def downgrade() -> None:
    # Drop the column on downgrade
    op.drop_column('user_portfolios', 'avg_cost')
