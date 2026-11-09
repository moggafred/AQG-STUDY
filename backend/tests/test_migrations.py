from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text


def test_migrations_upgrade_existing_database_without_losing_rows(tmp_path, monkeypatch):
    database_path = tmp_path / 'migration.db'
    database_url = f'sqlite:///{database_path.as_posix()}'
    monkeypatch.setenv('DATABASE_URL', database_url)
    config = Config(str(Path(__file__).parents[1] / 'alembic.ini'))

    command.upgrade(config, '0001_initial')
    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(text(
            "INSERT INTO users "
            "(id, email, full_name, provider, is_verified, created_at, last_login) "
            "VALUES ('kept', 'kept@example.test', 'Existing User', 'local', 1, "
            'CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)'
        ))
    engine.dispose()

    command.upgrade(config, 'head')
    command.upgrade(config, 'head')
    command.check(config)
    engine = create_engine(database_url)
    inspector = inspect(engine)
    assert {
        'document_chunks',
        'question_quality_reviews',
        'quiz_generation_runs',
        'question_ratings',
    } <= set(inspector.get_table_names())
    assert {'embedding', 'embedding_model'} <= {
        column['name'] for column in inspector.get_columns('document_chunks')
    }
    with engine.connect() as connection:
        assert connection.execute(
            text("SELECT full_name FROM users WHERE id = 'kept'")
        ).scalar_one() == 'Existing User'
    engine.dispose()
