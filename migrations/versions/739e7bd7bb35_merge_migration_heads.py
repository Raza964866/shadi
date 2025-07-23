"""Merge migration heads

Revision ID: 739e7bd7bb35
Revises: add_marital_status_001, remove_age_income
Create Date: 2025-07-20 19:13:27.446298

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '739e7bd7bb35'
down_revision = ('add_marital_status_001', 'remove_age_income')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
