"""Add CNIC field to user profiles

Revision ID: add_cnic_field
Revises: 854c4c59cdf0
Create Date: 2025-07-20 08:07:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_cnic_field'
down_revision = '854c4c59cdf0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user_profiles', sa.Column('cnic', sa.String(length=20), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user_profiles', 'cnic')
    # ### end Alembic commands ###
