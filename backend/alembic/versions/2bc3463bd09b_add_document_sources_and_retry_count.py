
"""add document sources and retry count"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '2bc3463bd09b'
down_revision: Union[str, Sequence[str], None] = 'ebf8f3e9160d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Create document_sources if missing
    if 'document_sources' not in inspector.get_table_names():

        op.create_table(
            'document_sources',
            sa.Column('id', sa.String(36), nullable=False),
            sa.Column('document_id', sa.String(36), nullable=False),
            sa.Column('source_type', sa.String(40), nullable=False),
            sa.Column('source_reference', sa.String(1000), nullable=False),
            sa.Column('source_metadata', sa.JSON(), nullable=True),
            sa.Column('status', sa.String(30), nullable=False),
            sa.Column('file_hash', sa.String(64), nullable=True),
            sa.Column('error_message', sa.String(2000), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(
                ['document_id'],
                ['documents.id'],
                ondelete='CASCADE'
            ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint(
                'source_type',
                'source_reference',
                name='uq_document_source_reference'
            )
        )

    # Refresh inspector after table creation
    inspector = sa.inspect(conn)

    # Create missing indexes
    if 'document_sources' in inspector.get_table_names():

        existing_indexes = {
            index['name']
            for index in inspector.get_indexes('document_sources')
        }

        indexes = [
            ('ix_document_sources_document_id', ['document_id']),
            ('ix_document_sources_file_hash', ['file_hash']),
            ('ix_document_sources_source_type', ['source_type']),
            ('ix_document_sources_status', ['status']),
            ('ix_document_sources_type_reference',
             ['source_type', 'source_reference']),
        ]

        for name, columns in indexes:
            if name not in existing_indexes:
                op.create_index(
                    name,
                    'document_sources',
                    columns,
                    unique=False
                )

    # Add retry_count only if missing
    inspector = sa.inspect(conn)

    existing_columns = {
        column['name']
        for column in inspector.get_columns('processing_jobs')
    }

    if 'retry_count' not in existing_columns:
        op.add_column(
            'processing_jobs',
            sa.Column(
                'retry_count',
                sa.Integer(),
                nullable=False,
                server_default=sa.text('0')
            )
        )


def downgrade() -> None:
    # This migration may encounter pre-existing objects.
    # Avoid deleting potentially pre-existing data or schema.
    pass
