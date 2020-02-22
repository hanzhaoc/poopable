"""add last_update to poopable

Revision ID: 06a9c825828a
Revises: 089557452cd9
Create Date: 2020-02-21 19:18:52.050571

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '06a9c825828a'
down_revision = '089557452cd9'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('poopable', sa.Column('last_update', sa.String(length=10), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('poopable', 'last_update')
    # ### end Alembic commands ###