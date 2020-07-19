"""Add back applicable_date to form_distribution, but as Date type

Revision ID: d3a4402a7d62
Revises: 4aaa5ba83bf5
Create Date: 2020-02-17 13:49:14.976725

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd3a4402a7d62'
down_revision = '4aaa5ba83bf5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('form_distribution', sa.Column('applicable_date', sa.Date(), nullable=False))
    op.create_index('class_date_index', 'form_distribution', ['class_section_id', 'applicable_date'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('class_date_index', table_name='form_distribution')
    op.drop_column('form_distribution', 'applicable_date')
    # ### end Alembic commands ###