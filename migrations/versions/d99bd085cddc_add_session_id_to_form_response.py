"""add session id to form response

Revision ID: d99bd085cddc
Revises: c6b71c4167a1
Create Date: 2020-02-17 16:33:14.677600

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd99bd085cddc'
down_revision = 'c6b71c4167a1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('form_response', sa.Column('class_section_student_id', sa.Integer(), nullable=False))
    op.add_column('form_response', sa.Column('session_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_form_response_class_section_student_id'), 'form_response', ['class_section_student_id'], unique=False)
    op.create_index(op.f('ix_form_response_session_id'), 'form_response', ['session_id'], unique=False)
    op.drop_index('ix_form_response_student_id', table_name='form_response')
    op.drop_constraint('form_response_student_id_fkey', 'form_response', type_='foreignkey')
    op.create_foreign_key(None, 'form_response', 'class_section_student', ['class_section_student_id'], ['id'])
    op.create_foreign_key(None, 'form_response', 'tutoring_session', ['session_id'], ['id'])
    op.drop_column('form_response', 'student_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('form_response', sa.Column('student_id', sa.INTEGER(), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'form_response', type_='foreignkey')
    op.drop_constraint(None, 'form_response', type_='foreignkey')
    op.create_foreign_key('form_response_student_id_fkey', 'form_response', 'class_section_student', ['student_id'], ['id'])
    op.create_index('ix_form_response_student_id', 'form_response', ['student_id'], unique=False)
    op.drop_index(op.f('ix_form_response_session_id'), table_name='form_response')
    op.drop_index(op.f('ix_form_response_class_section_student_id'), table_name='form_response')
    op.drop_column('form_response', 'session_id')
    op.drop_column('form_response', 'class_section_student_id')
    # ### end Alembic commands ###