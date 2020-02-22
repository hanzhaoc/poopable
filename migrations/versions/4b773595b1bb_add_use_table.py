"""add use table

Revision ID: 4b773595b1bb
Revises: b50a36a67bf9
Create Date: 2020-02-22 00:17:02.976360

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4b773595b1bb'
down_revision = 'b50a36a67bf9'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user',
    sa.Column('slack_user_id', sa.String(length=9), nullable=False),
    sa.PrimaryKeyConstraint('slack_user_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('user')
    # ### end Alembic commands ###