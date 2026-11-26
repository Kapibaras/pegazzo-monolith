"""document_analysis table and document.analysis_id (PGZ-179)

Temporary analyses of files uploaded before their entity exists, and the link from each promoted document to the
analysis it came from.

Revision ID: c3e8a1f5d7b2
Revises: b9d5f2a7c3e1
Create Date: 2026-11-26 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c3e8a1f5d7b2'
down_revision: Union[str, Sequence[str], None] = 'b9d5f2a7c3e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create document_analysis and add document.analysis_id."""
    op.create_table(
        'document_analysis',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('declared_type', sa.String(length=40), nullable=False),
        sa.Column('files', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('reason', sa.String(length=50), nullable=True),
        sa.Column('detected_type', sa.String(length=40), nullable=True),
        sa.Column('extracted_fields', sa.JSON(), nullable=True),
        sa.Column('prefill', sa.JSON(), nullable=True),
        sa.Column('model_version', sa.String(length=50), nullable=True),
        sa.Column('input_tokens', sa.Integer(), nullable=True),
        sa.Column('output_tokens', sa.Integer(), nullable=True),
        sa.Column('estimated_cost', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('created_by', sa.String(length=30), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('analyzed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('consumed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['user.username']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_document_analysis_status_created_at', 'document_analysis', ['status', 'created_at'], unique=False)

    op.add_column('document', sa.Column('analysis_id', sa.Uuid(), nullable=True))
    op.create_index(op.f('ix_document_analysis_id'), 'document', ['analysis_id'], unique=False)
    op.create_foreign_key(
        'fk_document_analysis_id_document_analysis',
        'document',
        'document_analysis',
        ['analysis_id'],
        ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    """Drop document.analysis_id and document_analysis."""
    op.drop_constraint('fk_document_analysis_id_document_analysis', 'document', type_='foreignkey')
    op.drop_index(op.f('ix_document_analysis_id'), table_name='document')
    op.drop_column('document', 'analysis_id')

    op.drop_index('ix_document_analysis_status_created_at', table_name='document_analysis')
    op.drop_table('document_analysis')
