"""empty message

Revision ID: 35665e680f24
Revises: f44966398da3
Create Date: 2020-02-09 14:05:48.641237

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '35665e680f24'
down_revision = 'f44966398da3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('tutoring_session',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('guide_id', sa.Integer(), nullable=False),
    sa.Column('learner_id', sa.Integer(), nullable=False),
    sa.Column('start_time', sa.DateTime(), nullable=False),
    sa.Column('end_time', sa.DateTime(), nullable=True),
    sa.Column('cancellation_reason', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['guide_id'], ['class_section_student.id'], ),
    sa.ForeignKeyConstraint(['learner_id'], ['class_section_student.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('tutoring_session')
    # ### end Alembic commands ###
