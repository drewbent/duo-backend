"""Initial migration

Revision ID: f44966398da3
Revises: 
Create Date: 2020-02-05 20:38:11.854713

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f44966398da3'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('class_section',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('ka_id', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_class_section_ka_id'), 'class_section', ['ka_id'], unique=True)
    op.create_table('class_section_student',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('email', sa.String(), nullable=True),
    sa.Column('firebase_id', sa.String(), nullable=True),
    sa.Column('signed_up_at', sa.DateTime(), nullable=True),
    sa.Column('class_section_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('archived_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['class_section_id'], ['class_section.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_class_section_student_class_section_id'), 'class_section_student', ['class_section_id'], unique=False)
    op.create_index(op.f('ix_class_section_student_email'), 'class_section_student', ['email'], unique=True)
    op.create_index(op.f('ix_class_section_student_name'), 'class_section_student', ['name'], unique=False)
    op.create_table('ka_skill_completion',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('student_id', sa.Integer(), nullable=False),
    sa.Column('course', sa.String(), nullable=True),
    sa.Column('unit', sa.String(), nullable=True),
    sa.Column('skill', sa.String(), nullable=False),
    sa.Column('questions_correct', sa.Integer(), nullable=True),
    sa.Column('questions_out_of', sa.Integer(), nullable=True),
    sa.Column('mastery_category', sa.String(), nullable=True),
    sa.Column('mastery_points', sa.Integer(), nullable=True),
    sa.Column('mastery_points_out_of', sa.Integer(), nullable=True),
    sa.Column('recorded_from', sa.Enum('teacher_dashboard', 'unit_view', 'unit_view_task', 'lesson_view_task', name='kaskillcompletionsource'), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['student_id'], ['class_section_student.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ka_skill_completion_skill'), 'ka_skill_completion', ['skill'], unique=False)
    op.create_index(op.f('ix_ka_skill_completion_student_id'), 'ka_skill_completion', ['student_id'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_ka_skill_completion_student_id'), table_name='ka_skill_completion')
    op.drop_index(op.f('ix_ka_skill_completion_skill'), table_name='ka_skill_completion')
    op.drop_table('ka_skill_completion')
    op.drop_index(op.f('ix_class_section_student_name'), table_name='class_section_student')
    op.drop_index(op.f('ix_class_section_student_email'), table_name='class_section_student')
    op.drop_index(op.f('ix_class_section_student_class_section_id'), table_name='class_section_student')
    op.drop_table('class_section_student')
    op.drop_index(op.f('ix_class_section_ka_id'), table_name='class_section')
    op.drop_table('class_section')
    # ### end Alembic commands ###
