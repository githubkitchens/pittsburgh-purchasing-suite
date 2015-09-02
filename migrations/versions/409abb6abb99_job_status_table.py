"""job_status_table

Revision ID: 409abb6abb99
Revises: 3f80f0c8adf1
Create Date: 2015-09-01 17:05:02.609696

"""

# revision identifiers, used by Alembic.
revision = '409abb6abb99'
down_revision = '3f80f0c8adf1'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('job_status',
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('date', sa.DateTime(), nullable=False),
    sa.Column('status', sa.String(), nullable=True),
    sa.Column('info', sa.Text(), nullable=True),
    sa.Column('updated_by_id', sa.Integer(), nullable=True),
    sa.Column('created_by_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], name='created_by_id_fkey', use_alter=True),
    sa.ForeignKeyConstraint(['updated_by_id'], ['users.id'], name='updated_by_id_fkey', use_alter=True),
    sa.PrimaryKeyConstraint('name', 'date')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('job_status')
    ### end Alembic commands ###
