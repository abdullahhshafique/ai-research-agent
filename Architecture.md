# Architecture — AI Research Agent

## High-Level Diagram

```
Browser
  │  HTTP / SSE
  ▼
Django (Gunicorn / runserver)
  ├── Middleware stack
  │     ├── WhiteNoise (static files)
  │     ├── CSP, HSTS, RateLimit, Quota
  │     └── Session / Auth
  ├── URL router → App views
  │     ├── accounts  (auth, home)
  │     ├── research  (submit, stream, retry, cancel)
  │     ├── reports   (download PDF)
  │     ├── history
  │     ├── collaboration
  │     ├── templates_app
  │     └── dashboard
  ├── In-process Job Queue (threading)
  │     └── Worker thread → Pipeline
  │           ├── SearchAgent  ──► Tavily API
  │           ├── TextChunker
  │           ├── Summarizer   ──► Groq API (Llama 3.3 70B)
  │           │                    └─ fallback ► Gemini API
  │           ├── ReportBuilder
  │           └── PDFExporter  ──► media/reports/*.pdf
  └── Database (SQLite dev / PostgreSQL prod)
        ├── accounts_user / accounts_profile
        ├── research_query / research_source
        └── reports_generatedreport
```

---

## Design Principles & Constraints

- **Stdlib-first HTTP** — no `requests` or `httpx`; custom `HTTPClient` wraps `urllib` to minimise dependencies
- **Single-process, thread-based concurrency** — job queue uses Python `threading`; acceptable for free-tier single-dyno deployment
- **Stateless views** — all state in DB; SSE endpoint reads from job queue, not memory
- **12-factor config** — all secrets via environment variables, never in code
- **Free-tier deployable** — no Redis, no Celery, no paid add-ons required

---

## Component Breakdown

| Component | Responsibility | Technology |
|---|---|---|
| `config/settings.py` | Central config, env loading | Django settings, python-dotenv |
| `apps/accounts` | Auth, custom User, Profile, quota | Django auth, signals |
| `apps/research` | Query lifecycle, pipeline orchestration, SSE | Django views, threading |
| `apps/reports` | PDF generation, report model | fpdf2 |
| `apps/history` | Read-only history views | Django views |
| `apps/collaboration` | Shared research (future) | Django models/views |
| `apps/templates_app` | Saved query templates | Django models/views |
| `apps/dashboard` | Admin UI, API key mgmt, log viewer | Django views |
| `apps/utils` | Middleware, rate limiter, health check, HTTP client | Pure Python |
| `services/pipeline.py` | Orchestrates search → chunk → summarise → report → PDF | Python |
| `services/search.py` | Tavily API wrapper, file-based cache | Python, stdlib |
| `services/summarizer.py` | Groq + Gemini LLM calls, chunked merge | Python, stdlib |

---

## Data Model

```
User (AbstractUser)
  │ 1:1
  └── Profile
        ├── role: free | premium | admin
        ├── quota_limit: int
        ├── used_quota: int
        └── quota_reset_at: datetime

ResearchQuery
  ├── user: FK → User
  ├── query_text: text
  ├── status: pending | processing | completed | failed
  ├── search_depth: basic | advanced
  ├── max_results: int
  ├── llm_model: groq | gemini
  ├── summary: text
  ├── final_insight: text
  ├── raw_sources: JSON
  ├── error_message: text
  ├── version: int
  ├── parent_query: FK → self (nullable)
  ├── is_latest: bool
  └── timestamps: created_at, started_at, completed_at

Source
  └── FK → ResearchQuery

GeneratedReport
  └── FK → ResearchQuery
        ├── pdf_file: FileField (media/reports/)
        └── created_at
```

---

## API Design

All endpoints are Django HTML views (session auth). No REST API in MVP.

| Method | URL | Auth | Description |
|---|---|---|---|
| GET | `/` | Optional | Home / landing |
| GET/POST | `/accounts/login/` | No | Login |
| GET/POST | `/accounts/register/` | No | Register |
| POST | `/accounts/logout/` | Yes | Logout |
| POST | `/research/submit/` | Yes | Submit query, returns `query_id` |
| GET | `/research/status/<id>/` | Yes | JSON status poll |
| GET | `/research/stream/<id>/` | Yes | SSE progress stream |
| POST | `/research/retry/<id>/` | Yes | Retry failed query |
| POST | `/research/cancel/<id>/` | Yes | Cancel pending query |
| GET | `/reports/download/<id>/` | Yes | Download PDF |
| GET | `/history/` | Yes | Research history list |
| GET | `/dashboard/` | Staff | Admin dashboard |
| GET | `/health/` | No | Health check (JSON) |

### SSE Event Format
```
event: status
data: {"progress": 45, "message": "Summarising sources..."}

event: complete
data: {"query_id": 123, "report_url": "/reports/download/123/"}

event: error
data: {"message": "Search returned no results"}
```

---

## Data Flow — Research Pipeline

```
POST /research/submit/
  → validate form
  → check quota (Profile.can_make_query())
  → create ResearchQuery(status=pending)
  → enqueue job(query_id) in JobQueue
  → return {query_id}

Browser opens GET /research/stream/<id>/
  → SSE response (text/event-stream)
  → reads progress from JobQueue

Worker thread:
  1. SearchAgent.search(query_text)        [5–25%]
     → Tavily API → cache check → return sources
  2. Save Source records to DB             [25–50%]
     → TextChunker.chunk(content) if > 60 KB
  3. Summarizer.summarise(chunks)          [50–80%]
     → Groq API → on failure → Gemini API
     → multi-chunk: per-chunk → merge pass
  4. ReportBuilder.build(summary, sources) [80–90%]
     → Markdown string
  5. PDFExporter.export(markdown)          [90–100%]
     → fpdf2 → save to media/reports/
     → create GeneratedReport record
  6. ResearchQuery.status = completed
```

---

## State Management

- **Backend state:** DB-only; no in-memory shared state between requests
- **Job progress:** In-process `JobQueue` dict keyed by `query_id`; acceptable for single-process deployment
- **Sessions:** Django DB-backed sessions
- **Caching:** File-based `SearchCache` for Tavily results (avoids duplicate API calls on retry)
- **Frontend state:** Minimal — SSE drives progress bar; no JS framework

---

## Security Architecture

| Concern | Implementation |
|---|---|
| HTTPS | Enforced in prod via `SECURE_SSL_REDIRECT`, HSTS |
| CSRF | Django `CsrfViewMiddleware` on all POST endpoints |
| CSP | `ContentSecurityPolicyMiddleware` — restricts script/style sources |
| Auth | Session-based; `@login_required` on all research/report views |
| API keys | Env vars only; passed via `Authorization: Bearer` header, never URL params |
| Rate limiting | `RateLimitMiddleware` — 60/hr anon, 300/hr auth |
| Quota | `QuotaMiddleware` + `Profile.can_make_query()` |
| Input validation | Django form validation on query submission |
| File access | PDF downloads gated behind `@login_required` + ownership check |
| Secret key | Env var; insecure default only for local dev |

---

## Deployment & Infrastructure

```
Local dev:   python manage.py runserver  (SQLite, DEBUG=True)
Production:  Render free tier
  ├── Web service: Gunicorn (config/wsgi.py)
  │     start command: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
  ├── Static files: WhiteNoise (CompressedManifestStaticFilesStorage)
  ├── Media files: local disk (ephemeral on Render free tier — PDFs lost on redeploy)
  └── Database: Render PostgreSQL free tier (dj-database-url)
```

**Environment variables required in production:**
`SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS`, `DATABASE_URL`, `GROQ_API_KEY`, `TAVILY_API_KEY`, `GOOGLE_API_KEY`, `CSRF_TRUSTED_ORIGINS`

---

## Error Handling & Resilience

- LLM timeout → automatic fallback from Groq to Gemini
- Both LLMs fail → `ResearchQuery.status = failed`, `error_message` stored, user can retry
- Tavily returns empty results → pipeline fails with descriptive error
- Worker thread exception → caught at pipeline level, status set to `failed`
- SSE client disconnects → server-side generator exits cleanly on `GeneratorExit`
- DB errors → Django's standard exception handling; 500 page in prod

---

## Testing Strategy

- **Unit tests:** Service layer (`SearchAgent`, `Summarizer`, `ReportBuilder`, `PDFExporter`) with mocked API calls
- **Integration tests:** Pipeline end-to-end with Tavily/Groq mocked at HTTP level
- **View tests:** Django `TestClient` for auth flows, quota enforcement, SSE endpoint
- **No E2E browser tests** in MVP (Playwright/Selenium deferred to Phase 3)
- Test files: `apps/<app>/tests.py` or `apps/<app>/tests/`

---

## Technical Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Render free tier spins down after 15 min inactivity | First request is slow (~30 s cold start) | Acceptable for MVP; upgrade to paid if needed |
| Render free PostgreSQL expires after 90 days | Data loss | Export DB before expiry; migrate to paid or Supabase free tier |
| In-process job queue lost on dyno restart | Pending jobs lost | Acceptable for MVP; migrate to Redis/Celery for production scale |
| Groq rate limits | Pipeline failures at scale | Gemini fallback; per-user quota limits abuse |
| PDF media files ephemeral on Render | Reports lost on redeploy | Store PDFs in S3/R2 for production (Phase 2) |
| Single-process threading | CPU-bound summarisation blocks other requests | Acceptable for low traffic; Gunicorn workers mitigate partially |
