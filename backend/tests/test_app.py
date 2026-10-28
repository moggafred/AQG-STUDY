from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest
import httpx
from fastapi import HTTPException
from fastapi.testclient import TestClient
from openai import RateLimitError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app, request_openai_json
from app.database import Base, get_db
from app.document_pipeline import (
    DocumentProcessingError,
    ExtractedPage,
    extract_pdf_pages,
    retrieve_relevant_chunks,
    split_pages,
)
from app.main import enforce_generation_rate_limit, generate_question_set, grade_answer

@pytest.fixture
def client(tmp_path, monkeypatch):
    test_engine = create_engine(
        f'sqlite:///{tmp_path / "aqg-test.db"}',
        connect_args={'check_same_thread': False},
    )
    Base.metadata.create_all(bind=test_engine)
    test_session = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    def override_get_db():
        db = test_session()
        try:
            yield db
        finally:
            db.close()

    monkeypatch.setattr('app.main.engine', test_engine)
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    test_engine.dispose()


def unique_email(prefix: str) -> str:
    return f'{prefix}-{uuid4().hex[:8]}@example.com'


def test_health(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'


def test_register_and_login(client):
    email = unique_email('user')
    register_data = {'full_name': 'Test User', 'email': email, 'password': 'password123'}
    response = client.post('/api/auth/register', json=register_data)
    assert response.status_code == 200, response.json()
    body = response.json()
    assert 'access_token' in body
    assert body['user']['email'] == email

    login_response = client.post('/api/auth/login', json={'email': email, 'password': 'password123'})
    assert login_response.status_code == 200
    assert 'access_token' in login_response.json()


def test_document_and_quiz_flow(client, monkeypatch):
    monkeypatch.setattr('app.main.request_openai_json', lambda instructions, input_text: {
        'questions': [{
            'question_text': f'Question {index + 1} about AI ethics?',
            'question_type': 'multiple_choice',
            'difficulty': 'intermediate',
            'options': ['Fairness', 'Irrelevant option'],
            'correct_answer': 'Fairness',
            'explanation': 'Fairness is a key AI ethics concept.',
        } for index in range(2)]
    })
    email = unique_email('doc')
    token = client.post('/api/auth/register', json={'full_name': 'Doc User', 'email': email, 'password': 'password123'}).json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    upload = client.post('/api/documents/upload', json={'title': 'AI Ethics', 'content': 'Artificial intelligence ethics focuses on bias, fairness, transparency, and accountability in learning systems.', 'filename': 'ethics.txt'}, headers=headers)
    assert upload.status_code == 200, upload.text
    document_id = upload.json()['document']['id']
    assert document_id

    quiz = client.post('/api/quizzes/generate', json={'topic': 'AI Ethics', 'question_type': 'multiple_choice', 'difficulty': 'intermediate', 'count': 2}, headers=headers)
    assert quiz.status_code == 200, quiz.text
    quiz_id = quiz.json()['quiz']['id']
    assert quiz_id
    assert 'correct_answer' not in quiz.json()['questions'][0]
    saved_quiz = client.get(f'/api/quizzes/{quiz_id}', headers=headers)
    assert saved_quiz.status_code == 200
    assert 'correct_answer' not in saved_quiz.json()['questions'][0]

    assessment = client.post('/api/assessments/submit', json={'quiz_id': quiz_id, 'answers': []}, headers=headers)
    assert assessment.status_code == 200
    assert assessment.json()['results'][0]['correct_answer'] == 'Fairness'


def test_performance_requires_auth(client):
    response = client.get('/api/performance')
    assert response.status_code == 401


def test_generation_requires_openai_key(client, monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    token = client.post('/api/auth/register', json={
        'full_name': 'AI Test User',
        'email': unique_email('ai-missing-key'),
        'password': 'password123',
    }).json()['access_token']

    response = client.post(
        '/api/quizzes/generate',
        json={'topic': 'Ecology', 'count': 1},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 503
    assert 'OPENAI_API_KEY' in response.json()['detail']


def test_openai_json_request_uses_server_key_and_json_mode(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'test-key-not-a-real-secret')

    class FakeOpenAI:
        def __init__(self, **kwargs):
            assert kwargs == {
                'api_key': 'test-key-not-a-real-secret',
                'timeout': 30.0,
                'max_retries': 0,
            }

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return None

        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    assert kwargs['response_format'] == {'type': 'json_object'}
                    return SimpleNamespace(
                        choices=[SimpleNamespace(
                            message=SimpleNamespace(content='{"ready": true}')
                        )]
                    )

    monkeypatch.setattr('app.main.OpenAI', FakeOpenAI)
    assert request_openai_json('Make JSON.', 'test input') == {'ready': True}


def test_openai_quota_error_has_actionable_configuration_message(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'test-key-not-a-real-secret')
    response = httpx.Response(
        429,
        request=httpx.Request('POST', 'https://api.openai.com/v1/chat/completions'),
    )
    quota_error = RateLimitError(
        'quota exhausted',
        response=response,
        body={'error': {'code': 'insufficient_quota', 'type': 'insufficient_quota'}},
    )

    class FakeOpenAI:
        def __init__(self, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return None

        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    raise quota_error

    monkeypatch.setattr('app.main.OpenAI', FakeOpenAI)
    with pytest.raises(HTTPException) as error:
        request_openai_json('Make JSON.', 'test input')
    assert error.value.status_code == 503
    assert 'no remaining quota' in error.value.detail


def test_quiz_and_study_resource_generation_use_mocked_openai(client, monkeypatch):
    def fake_openai_response(instructions, input_text):
        if 'Create a summary learning resource' in instructions:
            return {'summary': 'A concise summary from the supplied material.'}
        return {
            'questions': [{
                'question_text': 'Which ecosystem component produces food through photosynthesis?',
                'question_type': 'multiple_choice',
                'difficulty': 'intermediate',
                'options': ['Producers', 'Consumers'],
                'correct_answer': 'Producers',
                'explanation': 'Producers convert light energy into chemical energy.',
            }]
        }

    monkeypatch.setattr('app.main.request_openai_json', fake_openai_response)
    token = client.post('/api/auth/register', json={
        'full_name': 'AI Mock User',
        'email': unique_email('ai-mock'),
        'password': 'password123',
    }).json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    quiz_response = client.post(
        '/api/quizzes/generate',
        json={'topic': 'Ecosystems', 'count': 1, 'source_text': 'Producers use photosynthesis.'},
        headers=headers,
    )
    assert quiz_response.status_code == 200, quiz_response.text
    assert 'correct_answer' not in quiz_response.json()['questions'][0]

    resource_response = client.post(
        '/api/study_resources/generate',
        json={'kind': 'summary', 'topic': 'Ecosystems', 'source_text': 'Producers use photosynthesis.'},
        headers=headers,
    )
    assert resource_response.status_code == 200, resource_response.text
    assert resource_response.json()['resource']['content']['summary'].startswith('A concise summary')


def test_pdf_extraction_chunks_and_retrieval():
    import fitz

    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((72, 72), 'Photosynthesis converts light energy into chemical energy in plants.')
    content = pdf.tobytes()
    pdf.close()

    extracted = extract_pdf_pages(content)
    assert extracted == [
        ExtractedPage(
            page_number=1,
            text='Photosynthesis converts light energy into chemical energy in plants.',
        )
    ]
    chunks = split_pages(extracted, max_words=5, overlap_words=1)
    assert len(chunks) > 1
    retrieved = retrieve_relevant_chunks(
        'chemical energy',
        [(chunk.text, chunk.page_number) for chunk in chunks],
        limit=1,
    )
    assert 'chemical energy' in retrieved[0][0]
    assert retrieved[0][1] == 1


def test_pdf_extraction_rejects_invalid_and_scanned_files():
    import fitz

    with pytest.raises(DocumentProcessingError):
        extract_pdf_pages(b'not a PDF')

    pdf = fitz.open()
    pdf.new_page()
    content = pdf.tobytes()
    pdf.close()
    with pytest.raises(DocumentProcessingError, match='No selectable text'):
        extract_pdf_pages(content)


def test_pdf_upload_endpoint_saves_document_and_page_chunks(client):
    import fitz

    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((72, 72), 'A sufficiently long sentence about photosynthesis and the conversion of light energy.')
    content = pdf.tobytes()
    pdf.close()
    token = client.post('/api/auth/register', json={
        'full_name': 'PDF Upload User',
        'email': unique_email('pdf-upload'),
        'password': 'password123',
    }).json()['access_token']

    response = client.post(
        '/api/documents/upload-file',
        data={'title': 'Photosynthesis Notes'},
        files={'file': ('lesson.pdf', content, 'application/pdf')},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body['page_count'] == 1
    assert body['chunk_count'] == 1
    assert body['document']['filename'] == 'lesson.pdf'


def test_pdf_upload_rejects_wrong_type_and_oversized_files(client, monkeypatch):
    token = client.post('/api/auth/register', json={
        'full_name': 'PDF Validation User',
        'email': unique_email('pdf-validation'),
        'password': 'password123',
    }).json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    wrong_type = client.post(
        '/api/documents/upload-file',
        data={'title': 'Unsupported file'},
        files={'file': ('notes.txt', b'plain text', 'text/plain')},
        headers=headers,
    )
    assert wrong_type.status_code == 415

    monkeypatch.setattr('app.main.MAX_UPLOAD_BYTES', 8)
    oversized = client.post(
        '/api/documents/upload-file',
        data={'title': 'Oversized PDF'},
        files={'file': ('large.pdf', b'%PDF-123456', 'application/pdf')},
        headers=headers,
    )
    assert oversized.status_code == 413


def test_document_deletion_is_owner_scoped(client):
    owner_token = client.post('/api/auth/register', json={
        'full_name': 'Document Owner',
        'email': unique_email('delete-owner'),
        'password': 'password123',
    }).json()['access_token']
    document = client.post(
        '/api/documents/upload',
        json={'title': 'Saved notes', 'content': 'This is enough text to save and later delete.'},
        headers={'Authorization': f'Bearer {owner_token}'},
    ).json()['document']
    other_token = client.post('/api/auth/register', json={
        'full_name': 'Other Learner',
        'email': unique_email('delete-other'),
        'password': 'password123',
    }).json()['access_token']

    denied = client.delete(
        f"/api/documents/{document['id']}",
        headers={'Authorization': f'Bearer {other_token}'},
    )
    assert denied.status_code == 404
    deleted = client.delete(
        f"/api/documents/{document['id']}",
        headers={'Authorization': f'Bearer {owner_token}'},
    )
    assert deleted.status_code == 200
    assert client.get('/api/documents', headers={'Authorization': f'Bearer {owner_token}'}).json() == []


def test_short_answers_require_normalized_exact_match():
    question = SimpleNamespace(question_type='short_answer', correct_answer='Photosynthesis.')
    assert grade_answer(question, ' photosynthesis ')
    assert not grade_answer(question, 'photosynthesis is a process')
    assert not grade_answer(question, '')


def test_generation_rate_limit_is_bounded_per_user():
    user_id = f'rate-limit-{uuid4().hex}'
    for _ in range(5):
        enforce_generation_rate_limit(user_id)
    with pytest.raises(HTTPException) as error:
        enforce_generation_rate_limit(user_id)
    assert getattr(error.value, 'status_code', None) == 429


def test_invalid_question_set_gets_one_bounded_repair(monkeypatch):
    responses = iter([
        {'questions': []},
        {'questions': [{
            'question_text': 'Which process converts light into chemical energy?',
            'question_type': 'multiple_choice',
            'difficulty': 'intermediate',
            'options': ['Photosynthesis', 'Respiration'],
            'correct_answer': 'Photosynthesis',
            'explanation': 'Photosynthesis stores light energy as chemical energy.',
        }]},
    ])
    calls = []

    def fake_response(instructions, input_text):
        calls.append(instructions)
        return next(responses)

    monkeypatch.setattr('app.main.request_openai_json', fake_response)
    questions = generate_question_set('Plants', 'multiple_choice', 'intermediate', 1, '')
    assert len(questions) == 1
    assert len(calls) == 2
    assert 'failed schema validation' in calls[1]


def test_generation_cannot_use_another_users_document(client):
    owner_token = client.post('/api/auth/register', json={
        'full_name': 'Document Owner',
        'email': unique_email('document-owner'),
        'password': 'password123',
    }).json()['access_token']
    document = client.post(
        '/api/documents/upload',
        json={'title': 'Private notes', 'content': 'This material belongs to its owner only.'},
        headers={'Authorization': f'Bearer {owner_token}'},
    ).json()['document']
    other_user_token = client.post('/api/auth/register', json={
        'full_name': 'Other User',
        'email': unique_email('other-user'),
        'password': 'password123',
    }).json()['access_token']

    response = client.post(
        '/api/quizzes/generate',
        json={'topic': 'Private notes', 'count': 1, 'document_id': document['id']},
        headers={'Authorization': f'Bearer {other_user_token}'},
    )

    assert response.status_code == 404


def test_google_login_does_not_trust_submitted_email(client):
    response = client.post('/api/auth/google', json={
        'email': unique_email('unverified-google'),
        'full_name': 'Unverified User',
    })
    assert response.status_code == 501
