# AQG — AI-Powered Educational Assessment and Study Platform

AQG is a local educational study platform built around FastAPI, SQLite, and a browser-native JavaScript frontend. Learners can save notes or upload text-based PDFs, create AI-generated quizzes and revision resources, complete assessments, and review saved results.

## What it does

- Email/password registration and JWT-authenticated personal workspaces.
- Text notes and PDF upload (10 MB default limit); selectable PDF text is extracted and indexed by page, and owners can delete their documents.
- Local TF-IDF vector retrieval selects relevant page chunks to provide as context for quiz and study-resource generation.
- Multiple-choice, true/false, short-answer, essay, scenario-based, case-study, application, and mixed quiz-generation requests.
- Summaries, flashcards, key concepts, revision notes, and definitions.
- Saved quizzes and resources, assessment attempts, answer feedback, and data-based performance summaries.
- Responsive static frontend; no frontend build step or external CDN is required.

## Architecture and RAG workflow

1. The frontend submits text or a PDF to the FastAPI backend.
2. The backend validates file type and size, extracts selectable text from each PDF page, splits it into overlapping chunks, and saves the document and page references in SQLite.
3. During generation, the backend creates TF-IDF vectors from the saved chunks and retrieves up to four chunks most relevant to the requested topic. The prompt includes retrieved page references so generated items can retain a source reference.
4. OpenAI returns JSON which is checked for required fields and basic answer-format validity before the result is saved.
5. Assessment submissions are marked and stored. Correct answers are returned only after submission; saved quiz views do not expose answer keys.

This is a lightweight local vector-retrieval implementation, not a hosted vector database or transformer-embedding pipeline. Scanned PDFs require OCR and are rejected with an explanatory error. AI generation requires an OpenAI API key and available API quota; tests mock the provider and do not spend API credits.

## Technology

- Python, FastAPI, Pydantic, SQLAlchemy, SQLite, PyMuPDF, Pytest
- OpenAI Chat Completions JSON mode for quiz and resource generation
- Static HTML, CSS, and JavaScript for the frontend

## Repository layout

```text
backend/
  app/
    database.py
    document_pipeline.py
    main.py
    models.py
    schemas.py
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
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In another terminal, serve the frontend:

```powershell
Set-Location frontend
python -m http.server 4173
```

Open <http://localhost:4173>. The default backend URL is `http://127.0.0.1:8000`; the static frontend reads an optional `window.AQG_API_BASE_URL` override. Configure `ALLOWED_ORIGINS` in `.env` to include the origin used by the browser.

The backend creates the SQLite tables on startup. By default, the database is `backend/aqg.db` when the backend is started from its folder. Set `DATABASE_URL` to use another SQLAlchemy database URL.

## Deploying with Vercel and Render

The frontend is a static site for Vercel. The FastAPI backend and persistent PostgreSQL database run on Render; the frontend and API are separate services.

1. Push the project to a GitHub repository. Keep `.env`, database files, virtual environments, and generated build output out of Git; `.gitignore` excludes them.
2. In Render, create a new Blueprint from the repository and use the root `render.yaml`. The blueprint configures the API and PostgreSQL database. The `starter` web-service plan and `basic-256mb` database plan can incur charges; review Render's current pricing before creating the services.
3. Configure `ALLOWED_ORIGINS` for the Render API with the exact Vercel site origin, such as `https://your-project.vercel.app` (no trailing slash). Include additional origins as comma-separated values if needed. Set `OPENAI_API_KEY` in Render only if AI generation is required; it can be left blank otherwise.
4. Copy the deployed API base URL from Render, for example `https://your-api.onrender.com`.
5. In Vercel, import the same GitHub repository. Keep the project root at the repository root so Vercel uses `vercel.json`. Add the environment variable `AQG_API_BASE_URL` with the Render API base URL for each environment you deploy (Production, Preview, and Development as applicable), then deploy.
6. Open the Vercel URL and verify the site and API. If you change the Vercel domain, update `ALLOWED_ORIGINS` in Render and redeploy/restart the API.

The Vercel build copies `frontend/` into `dist/` and generates `config.js` from `AQG_API_BASE_URL`. The local `frontend/config.js` continues to use `http://127.0.0.1:8000` for local development. Do not put backend secrets such as `SECRET_KEY` or `OPENAI_API_KEY` into Vercel or frontend files.

For a local production-build check in PowerShell:

```powershell
$env:AQG_API_BASE_URL = "https://your-api.onrender.com"
npm run build
```

The Render blueprint generates a production `SECRET_KEY` and connects the backend to managed PostgreSQL. It does not configure a live OpenAI key. Render and Vercel accounts, GitHub access, and any provider charges are separate from this repository setup.

## API routes

- `GET /health`
- `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`
- `GET /api/documents`, `POST /api/documents/upload` (text), `POST /api/documents/upload-file` (PDF), `DELETE /api/documents/{document_id}`
- `GET /api/quizzes`, `GET /api/quizzes/{quiz_id}`, `POST /api/quizzes/generate`
- `POST /api/study_resources/generate`, `GET /api/study_resources`
- `POST /api/assessments/submit`, `GET /api/assessments/history`, `GET /api/assessments/{attempt_id}`
- `GET /api/performance`

All personal routes require a bearer token. Google sign-in is deliberately disabled until a real OAuth identity-verification flow is configured.

## Tests

Run the backend tests from the backend folder:

```powershell
python -m pytest -q
```

Tests use isolated temporary SQLite databases and mock OpenAI responses; they do not require a paid API key. Live API generation should be tested separately only when the OpenAI API account has available quota.

## Configuration

| Variable | Purpose | Default |
|---|---|---|
| `SECRET_KEY` | JWT signing secret | Development-only fallback |
| `DATABASE_URL` | SQLAlchemy database URL | `sqlite:///./aqg.db` |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins | Local frontend/backend origins |
| `OPENAI_API_KEY` | Server-side key for generation | Empty / AI generation disabled |
| `OPENAI_MODEL` | OpenAI model | `gpt-4o-mini` |
| `MAX_UPLOAD_BYTES` | Maximum PDF size | `10485760` (10 MB) |
| `GENERATION_REQUESTS_PER_MINUTE` | In-process per-user generation limit | `5` |
| `AQG_API_BASE_URL` | Frontend build-time backend URL (Vercel) | Required for production builds |
| `ENVIRONMENT` | Set to `production` to require `SECRET_KEY` | Unset locally |

## Known limitations and future work

- OCR for image-only PDFs is not implemented.
- Retrieval uses local TF-IDF vectors; semantic embeddings and a persistent vector index are future improvements.
- Automatic grading is exact normalized matching. Essay and other open-ended responses are not represented as objectively AI-graded.
- The generation rate limiter is process-local; use shared storage for a multi-worker deployment. Account recovery, full Google OAuth, role management, database migrations, and deployment-specific durable storage are not yet implemented.
- Configure a managed database and deployment-grade secrets before hosting beyond local development. Do not rely on ephemeral local SQLite storage for a deployed service.
