"""Persist embeddings and research quality metadata.

Revision ID: 0002_embeddings_and_research
"""

from alembic import op
import sqlalchemy as sa

revision = '0002_embeddings_and_research'
down_revision = '0001_initial'
branch_labels = None
depends_on = None


def _tables() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _columns(table: str) -> set[str]:
    return {column['name'] for column in sa.inspect(op.get_bind()).get_columns(table)}


def upgrade() -> None:
    if 'document_chunks' in _tables():
        columns = _columns('document_chunks')
        if 'embedding' not in columns:
            op.add_column('document_chunks', sa.Column('embedding', sa.JSON(), nullable=True))
        if 'embedding_model' not in columns:
            op.add_column('document_chunks', sa.Column('embedding_model', sa.String(), nullable=True))
        if 'ix_document_chunks_document_id' not in {
            index['name'] for index in sa.inspect(op.get_bind()).get_indexes('document_chunks')
        }:
            op.create_index(
                'ix_document_chunks_document_id',
                'document_chunks',
                ['document_id'],
                unique=False,
            )

    if 'question_quality_reviews' not in _tables():
        op.create_table(
            'question_quality_reviews',
            sa.Column('question_id', sa.String(), sa.ForeignKey('questions.id'), primary_key=True),
            sa.Column('status', sa.String(), nullable=False),
            sa.Column('duplicate_of_question', sa.Integer(), nullable=True),
            sa.Column('source_support', sa.String(), nullable=False),
            sa.Column('source_overlap', sa.Float(), nullable=True),
            sa.Column('semantic_similarity', sa.Float(), nullable=True),
            sa.Column('review_note', sa.Text(), nullable=False),
        )
    elif 'semantic_similarity' not in _columns('question_quality_reviews'):
        op.add_column(
            'question_quality_reviews',
            sa.Column('semantic_similarity', sa.Float(), nullable=True),
        )

    if 'quiz_generation_runs' not in _tables():
        op.create_table(
            'quiz_generation_runs',
            sa.Column('quiz_id', sa.String(), sa.ForeignKey('quizzes.id'), primary_key=True),
            sa.Column('owner_id', sa.String(), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('generation_condition', sa.String(), nullable=False),
            sa.Column('source_document_id', sa.String(), nullable=True),
            sa.Column('retrieved_context', sa.Text(), nullable=False),
            sa.Column('generation_time_ms', sa.Integer(), nullable=False),
        )
    if 'ix_quiz_generation_runs_owner_id' not in {
        index['name'] for index in sa.inspect(op.get_bind()).get_indexes('quiz_generation_runs')
    }:
        op.create_index(
            'ix_quiz_generation_runs_owner_id',
            'quiz_generation_runs',
            ['owner_id'],
            unique=False,
        )

    if 'question_ratings' not in _tables():
        op.create_table(
            'question_ratings',
            sa.Column('id', sa.String(), primary_key=True),
            sa.Column('question_id', sa.String(), sa.ForeignKey('questions.id'), nullable=False),
            sa.Column('reviewer_id', sa.String(), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('relevance', sa.Integer(), nullable=False),
            sa.Column('source_alignment', sa.Integer(), nullable=False),
            sa.Column('answer_correctness', sa.Integer(), nullable=False),
            sa.Column('answerability', sa.Integer(), nullable=False),
            sa.Column('clarity', sa.Integer(), nullable=False),
            sa.Column('grammar', sa.Integer(), nullable=False),
            sa.Column('educational_usefulness', sa.Integer(), nullable=False),
            sa.Column('comment', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
        )
    for name, column in (
        ('ix_question_ratings_question_id', 'question_id'),
        ('ix_question_ratings_reviewer_id', 'reviewer_id'),
    ):
        if name not in {
            index['name'] for index in sa.inspect(op.get_bind()).get_indexes('question_ratings')
        }:
            op.create_index(name, 'question_ratings', [column], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    if 'question_ratings' in tables:
        op.drop_table('question_ratings')
    if 'quiz_generation_runs' in tables:
        op.drop_index('ix_quiz_generation_runs_owner_id', table_name='quiz_generation_runs')
        op.drop_table('quiz_generation_runs')
    if 'question_quality_reviews' in tables:
        if 'semantic_similarity' in _columns('question_quality_reviews'):
            op.drop_column('question_quality_reviews', 'semantic_similarity')
    if 'document_chunks' in tables:
        columns = _columns('document_chunks')
        if 'ix_document_chunks_document_id' in {
            index['name'] for index in sa.inspect(bind).get_indexes('document_chunks')
        }:
            op.drop_index('ix_document_chunks_document_id', table_name='document_chunks')
        if 'embedding_model' in columns:
            op.drop_column('document_chunks', 'embedding_model')
        if 'embedding' in columns:
            op.drop_column('document_chunks', 'embedding')
