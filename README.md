# AQG — AI-Powered Educational Assessment and Study Platform

AQG is a local educational study platform built around FastAPI, SQLite, and a browser-native JavaScript frontend. Learners can save notes or upload text-based PDFs, create AI-generated quizzes and revision resources, complete assessments, and review saved results.

## What it does

- Email/password registration and JWT-authenticated personal workspaces.
- Text notes and PDF upload (10 MB default limit); selectable PDF text is extracted and indexed by page, and owners can delete their documents.
- Configurable OpenAI-compatible text embeddings are persisted alongside page chunks and searched with cosine similarity; TF-IDF is the no-key fallback.
- Multiple-choice, true/false, short-answer, essay, scenario-based, case-study, application, and mixed quiz-generation requests.
- Summaries, flashcards, key concepts, revision notes, and definitions.
- Saved quizzes and resources, assessment attempts, answer feedback, and data-based performance summaries. Objective questions are auto-marked; essays and open-ended questions are saved for manual review.
- Question quality screening for invalid structure, near-duplicate questions, and lexical or embedding similarity to retrieved source text. These checks are screening signals, not proof of factual correctness.
- Research metadata for retrieval/no-retrieval quiz generation, seven human-rating dimensions, and a user-scoped CSV export.
- Responsive static frontend; no frontend build step or external CDN is required.

## Architecture and RAG workflow

1. The frontend submits text or a PDF to the FastAPI backend.
2. The backend validates file type and size, extracts selectable text from each PDF page, splits it into overlapping chunks, and saves the document and page references in SQLite.
3. During upload, the configured embedding provider converts page chunks into vectors stored with their document and page metadata in the relational database. During generation, the backend embeds the query and uses cosine similarity to retrieve up to four matching chunks from the selected, owner-authorized document. Legacy chunks are embedded on first retrieval when an embedding provider is configured. Queries below the configured threshold are rejected. If embeddings are not configured, TF-IDF retrieval is used instead.
4. OpenAI returns JSON which is checked against a Pydantic question schema, structural rules, duplicate screening, and source relevance screening. With embeddings enabled, the generated question and expected answer are compared to retrieved evidence by embedding similarity; without them lexical overlap is used. Neither method proves entailment, support, or correctness, so generated questions remain marked for human review.
5. Generation condition, source context, elapsed generation time, and reviewer ratings are stored for research export. Quiz and assessment data remain scoped to the owning user.
6. Objective assessment answers are marked and stored. Essay, case-study, scenario, and application answers are not falsely scored by exact-string matching and are flagged for manual review.

The persistent vectors currently live in a JSON column in the relational database and are cosine-searched in application code. This keeps local SQLite and PostgreSQL supported without requiring pgvector, but is intended for small-to-medium study collections; use pgvector or another indexed vector store for larger deployments. The embedding provider is behind a small interface, with OpenAI and OpenAI-compatible endpoints supported. Scanned PDFs require OCR and are rejected with an explanatory error. AI generation requires an OpenAI API key and available API quota; tests mock the provider and do not spend API credits.

## Technology

- Python, FastAPI, Pydantic, SQLAlchemy, Alembic, SQLite/PostgreSQL, PyMuPDF, Pytest
- OpenAI-compatible embeddings and Chat Completions JSON mode for generation
- Static HTML, CSS, and JavaScript for the frontend

## Repository layout

```text
backend/
  app/
    database.py
    document_pipeline.py
    embeddings.py
    main.py
    models.py
    question_validation.py
    schemas.py
  alembic/
  alembic.ini
  tests/
frontend/
  app.js
  index.html
  styles.css
.env.example
README.md
```

## Prerequisites

- Python 3.11 or later
- An OpenAI API account with API access and available quota for live generation

## Local setup on Windows

From the project root, copy the example configuration and edit `.env`:

```powershell
Copy-Item .env.example .env
notepad .env
```

Set a private `SECRET_KEY` and, for AI generation, a valid `OPENAI_API_KEY`. The key belongs only in the project-root `.env`; do not put it in `.env.example`, frontend code, or version control. `OPENAI_MODEL` defaults to `gpt-4o-mini`. API usage is billed separately from ChatGPT and requires available API quota.

Install and start the backend:

```powershell
Set-Location backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In another terminal, serve the frontend:

```powershell
Set-Location frontend
python -m http.server 4173
```

Open <http://localhost:4173>. The default backend URL is `http://127.0.0.1:8000`; the static frontend reads an optional `window.AQG_API_BASE_URL` override. Configure `ALLOWED_ORIGINS` in `.env` to include the origin used by the browser.

Alembic migrations create missing tables and apply compatible schema updates before the API starts. Run `alembic upgrade head` from the backend folder after installing dependencies. For an existing database, the initial migration skips tables that already exist and the following migration adds only missing columns/tables, preserving stored records. By default, the database is `backend/aqg.db` when the backend is started from its folder. Set `DATABASE_URL` to use another SQLAlchemy database URL.

## Free-tier deployment with Vercel, Render, and Neon

The frontend is a static site on Vercel Hobby, the FastAPI backend runs on Render's free web-service plan, and persistent PostgreSQL is hosted by Neon's free plan. This avoids a monthly hosting subscription within provider limits, but free services can sleep, pause, or have usage and storage caps. OpenAI API usage, if enabled, is billed separately.

1. Keep `.env`, database files, virtual environments, and generated build output out of Git; `.gitignore` excludes them.
2. Create a free PostgreSQL project on Neon. Copy its pooled connection string, including the SSL query options supplied by Neon.
3. In Render, create a Blueprint from this repository using the root `render.yaml`. The blueprint configures a free API service. In Render's environment settings, set `DATABASE_URL` to Neon's connection string and `ALLOWED_ORIGINS` initially to `http://localhost:4173`. Set `OPENAI_API_KEY` only if AI generation is required; it can remain unset otherwise.
4. Copy the deployed API base URL from Render, for example `https://your-api.onrender.com`.
5. In Vercel, import the same GitHub repository. Keep the project root at the repository root so Vercel uses `vercel.json`. Add the environment variable `AQG_API_BASE_URL` with the Render API base URL for each environment you deploy (Production, Preview, and Development as applicable), then deploy.
6. After Vercel provides the site URL, update Render's `ALLOWED_ORIGINS` to that exact origin, such as `https://your-project.vercel.app` (no trailing slash). Include additional origins as comma-separated values if needed, then redeploy/restart the API.
7. Open the Vercel URL and verify the site and API. If you change the Vercel domain, update `ALLOWED_ORIGINS` in Render and redeploy/restart the API.

The Vercel build copies `frontend/` into `dist/` and generates `config.js` from `AQG_API_BASE_URL`. The local `frontend/config.js` continues to use `http://127.0.0.1:8000` for local development. Do not put backend secrets such as `SECRET_KEY` or `OPENAI_API_KEY` into Vercel or frontend files.

For a local production-build check in PowerShell:

```powershell
$env:AQG_API_BASE_URL = "https://your-api.onrender.com"
npm run build
```

The Render blueprint generates a production `SECRET_KEY`; you provide the Neon `DATABASE_URL` and optionally an OpenAI key in Render's environment settings. The free Render web service sleeps after inactivity, and free database providers can pause or impose usage limits, so expect slower first requests and check provider limits before relying on this setup for important data. Keep backups of study data you cannot afford to lose. OpenAI API usage may incur separate charges.

## API routes

- `GET /health`
- `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`
- `GET /api/documents`, `POST /api/documents/upload` (text), `POST /api/documents/upload-file` (PDF), `DELETE /api/documents/{document_id}`
- `GET /api/quizzes`, `GET /api/quizzes/{quiz_id}`, `POST /api/quizzes/generate`
- `POST /api/study_resources/generate`, `GET /api/study_resources`
- `POST /api/assessments/submit`, `GET /api/assessments/history`, `GET /api/assessments/{attempt_id}`
- `GET /api/performance`
- `GET /api/research/results`, `GET /api/research/export.csv`, `POST /api/research/ratings`

All personal routes require a bearer token. Google sign-in is deliberately disabled until a real OAuth identity-verification flow is configured.
The research rating endpoint accepts relevance, source alignment, answer correctness, answerability, clarity, grammar, and educational usefulness ratings on a 1–5 scale. The CSV export is limited to the authenticated user's generation runs.

## Tests

Run the backend tests from the backend folder:

```powershell
python -m pytest -q
```

Tests use isolated temporary SQLite databases and mock OpenAI responses; they cover retrieval misses, quality screening, manual assessment review, research export, and ownership checks without requiring a paid API key. Live API generation should be tested separately only when the OpenAI API account has available quota.

## Configuration

| Variable | Purpose | Default |
|---|---|---|
| `SECRET_KEY` | JWT signing secret | Development-only fallback |
| `DATABASE_URL` | SQLAlchemy database URL | `sqlite:///./aqg.db` |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins | Local frontend/backend origins |
| `OPENAI_API_KEY` | Server-side key for generation | Empty / AI generation disabled |
| `OPENAI_MODEL` | OpenAI model | `gpt-4o-mini` |
| `EMBEDDING_PROVIDER` | Embedding provider mode (`auto`, `openai`, or `tfidf`) | `auto` |
| `EMBEDDING_API_KEY` | Embedding API key (falls back to `OPENAI_API_KEY`) | Empty |
| `EMBEDDING_BASE_URL` | Optional OpenAI-compatible embeddings endpoint | Provider default |
| `EMBEDDING_MODEL` | Embedding model identifier | `text-embedding-3-small` |
| `MAX_UPLOAD_BYTES` | Maximum PDF size | `10485760` (10 MB) |
| `GENERATION_REQUESTS_PER_MINUTE` | In-process per-user generation limit | `5` |
| `RETRIEVAL_TOP_K` | Maximum document chunks retrieved for generation | `4` |
| `MIN_RETRIEVAL_SCORE` | Minimum cosine score or lexical relevance score for retrieved chunks (0–1) | `0.25` |
| `AQG_API_BASE_URL` | Frontend build-time backend URL (Vercel) | Required for production builds |
| `ENVIRONMENT` | Set to `production` to require `SECRET_KEY` | Unset locally |

## Known limitations and future work

- OCR for image-only PDFs is not implemented.
- The default persistent vector storage is a JSON-backed relational index searched in application code, not a dedicated ANN index such as pgvector. It is not designed for very large corpora.
- Similarity screening is not entailment or a factuality guarantee, and intentionally leaves generated questions in human-review status. It does not automatically evaluate answer correctness, answerability, clarity, grammar, or educational usefulness.
- No reviewer outcome is fabricated. Human ratings are collected through the research endpoint and are only available where reviewers submit them.
- The generation rate limiter is process-local; use shared storage for a multi-worker deployment. Account recovery, full Google OAuth, role management, pgvector/ANN indexing, and deployment-specific durable file storage are not yet implemented. Alembic manages relational schema migrations.
- Configure a managed database and deployment-grade secrets before hosting beyond local development. Do not rely on ephemeral local SQLite storage for a deployed service.
