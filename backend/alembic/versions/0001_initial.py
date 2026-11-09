"""Create the original AQG relational schema when it is missing.

Revision ID: 0001_initial
"""

from alembic import op
import sqlalchemy as sa

revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def _create_if_missing(name: str, *columns, **kwargs) -> None:
    if name not in sa.inspect(op.get_bind()).get_table_names():
        op.create_table(name, *columns, **kwargs)


def upgrade() -> None:
    _create_if_missing(
        'users',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=True),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('is_verified', sa.Integer(), nullable=False),
        sa.Column('avatar_url', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_login', sa.DateTime(), nullable=False),
    )
    if 'ix_users_email' not in {
        index['name'] for index in sa.inspect(op.get_bind()).get_indexes('users')
    }:
        op.create_index('ix_users_email', 'users', ['email'], unique=True)

    _create_if_missing(
        'documents',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('owner_id', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('filename', sa.String(), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    _create_if_missing(
        'document_chunks',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('document_id', sa.String(), sa.ForeignKey('documents.id'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('source_page', sa.Integer(), nullable=True),
        sa.Column('chunk_index', sa.Integer(), nullable=True),
    )
    if 'ix_document_chunks_document_id' not in {
        index['name'] for index in sa.inspect(op.get_bind()).get_indexes('document_chunks')
    }:
        op.create_index(
            'ix_document_chunks_document_id',
            'document_chunks',
            ['document_id'],
            unique=False,
        )
    _create_if_missing(
        'quizzes',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('owner_id', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('topic', sa.String(), nullable=False),
        sa.Column('question_type', sa.String(), nullable=False),
        sa.Column('difficulty', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    _create_if_missing(
        'questions',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('quiz_id', sa.String(), sa.ForeignKey('quizzes.id'), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('question_type', sa.String(), nullable=False),
        sa.Column('difficulty', sa.String(), nullable=False),
        sa.Column('options', sa.JSON(), nullable=True),
        sa.Column('correct_answer', sa.Text(), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('source_reference', sa.String(), nullable=True),
        sa.Column('marks', sa.Integer(), nullable=True),
    )
    _create_if_missing(
        'assessment_attempts',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('quiz_id', sa.String(), sa.ForeignKey('quizzes.id'), nullable=False),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('score', sa.Integer(), nullable=True),
        sa.Column('total', sa.Integer(), nullable=True),
        sa.Column('percentage', sa.Integer(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(), nullable=False),
    )
    _create_if_missing(
        'assessment_answer_records',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('attempt_id', sa.String(), sa.ForeignKey('assessment_attempts.id'), nullable=False),
        sa.Column('question_id', sa.String(), nullable=False),
        sa.Column('user_answer', sa.Text(), nullable=True),
        sa.Column('is_correct', sa.Integer(), nullable=True),
        sa.Column('explanation', sa.Text(), nullable=True),
    )
    _create_if_missing(
        'study_resources',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('owner_id', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('kind', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('content', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    # This bootstrap revision also stamps pre-existing application databases.
    # Dropping its tables would therefore risk deleting user data.
    pass
