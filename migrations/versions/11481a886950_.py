"""empty message

Revision ID: 11481a886950
Revises: 120c5cdcb3d3
Create Date: 2020-09-17 00:21:55.012359

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '11481a886950'
down_revision = '120c5cdcb3d3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('Artist_seeking_talent_key', 'Artist', type_='unique')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint('Artist_seeking_talent_key', 'Artist', ['seeking_talent'])
    # ### end Alembic commands ###
