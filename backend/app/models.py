from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text

from app.database import Base


class User(Base):
    __tablename__ = 'users'
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    password_hash = Column(String, nullable=True)
    provider = Column(String, default='local', nullable=False)
    is_verified = Column(Integer, default=1, nullable=False)
    avatar_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, default=datetime.utcnow, nullable=False)


class Document(Base):
    __tablename__ = 'documents'
    id = Column(String, primary_key=True)
    owner_id = Column(String, ForeignKey('users.id'), nullable=False)
    title = Column(String, nullable=False)
    filename = Column(String, nullable=True)
    file_size = Column(Integer, default=0)
    status = Column(String, default='processed')
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class DocumentChunk(Base):
    __tablename__ = 'document_chunks'
    id = Column(String, primary_key=True)
    document_id = Column(String, ForeignKey('documents.id'), nullable=False)
    content = Column(Text, nullable=False)
    source_page = Column(Integer, default=1)
    chunk_index = Column(Integer, default=0)


class Quiz(Base):
    __tablename__ = 'quizzes'
    id = Column(String, primary_key=True)
    owner_id = Column(String, ForeignKey('users.id'), nullable=False)
    title = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    question_type = Column(String, nullable=False)
    difficulty = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Question(Base):
    __tablename__ = 'questions'
    id = Column(String, primary_key=True)
    quiz_id = Column(String, ForeignKey('quizzes.id'), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String, nullable=False)
    difficulty = Column(String, nullable=False)
    options = Column(JSON, nullable=True)
    correct_answer = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)
    source_reference = Column(String, nullable=True)
    marks = Column(Integer, default=1)


class AssessmentAttempt(Base):
    __tablename__ = 'assessment_attempts'
    id = Column(String, primary_key=True)
    quiz_id = Column(String, ForeignKey('quizzes.id'), nullable=False)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    score = Column(Integer, default=0)
    total = Column(Integer, default=0)
    percentage = Column(Integer, default=0)
    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class AssessmentAnswerRecord(Base):
    __tablename__ = 'assessment_answer_records'
    id = Column(String, primary_key=True)
    attempt_id = Column(String, ForeignKey('assessment_attempts.id'), nullable=False)
    question_id = Column(String, nullable=False)
    user_answer = Column(Text, nullable=True)
    is_correct = Column(Integer, default=0)
    explanation = Column(Text, nullable=True)


class StudyResource(Base):
    __tablename__ = 'study_resources'
    id = Column(String, primary_key=True)
    owner_id = Column(String, ForeignKey('users.id'), nullable=False)
    kind = Column(String, nullable=False)
    title = Column(String, nullable=False)
    content = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
