"""add role column on students table

Revision ID: b033ff7914c8
Revises: c5cd63bbf457
Create Date: 2025-10-22 15:11:00.086806
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b033ff7914c8'
down_revision = 'c5cd63bbf457'
branch_labels = None
depends_on = None


def upgrade():
    # 1️⃣ Create ENUM type first
    student_roles = sa.Enum('STUDENT', name='student_roles')
    student_roles.create(op.get_bind(), checkfirst=True)

    # 2️⃣ Now add the column using that ENUM type
    with op.batch_alter_table('students', schema=None) as batch_op:
        batch_op.add_column(sa.Column('role', student_roles, nullable=False, server_default='STUDENT'))
        batch_op.create_index(batch_op.f('ix_students_role'), ['role'], unique=False)


def downgrade():
    with op.batch_alter_table('students', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_students_role'))
        batch_op.drop_column('role')

    # Drop ENUM type on downgrade
    student_roles = sa.Enum('STUDENT', name='student_roles')
    student_roles.drop(op.get_bind(), checkfirst=True)
