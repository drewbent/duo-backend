"""Add manually_requested to tutoring session

Revision ID: be37c40a36c3
Revises: b8db000dbee9
Create Date: 2020-02-26 21:06:34.030064

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'be37c40a36c3'
down_revision = 'b8db000dbee9'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('tutoring_session', sa.Column('manually_requested', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('tutoring_session', 'manually_requested')
    # ### end Alembic commands ###
