"""Add indexes to question labels

Revision ID: 1f3ddc1d481e
Revises: 8baaf50e0f41
Create Date: 2020-02-12 21:48:32.162922

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1f3ddc1d481e'
down_revision = '8baaf50e0f41'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(op.f('ix_question_label_label_id'), 'question_label', ['label_id'], unique=False)
    op.create_index(op.f('ix_question_label_question_id'), 'question_label', ['question_id'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_question_label_question_id'), table_name='question_label')
    op.drop_index(op.f('ix_question_label_label_id'), table_name='question_label')
    # ### end Alembic commands ###
