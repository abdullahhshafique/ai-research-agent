# Memory — AI Research Agent

_Update this file at the end of every working session._

---

## Current Project State

Phase 0 (local dev setup) is complete. The server runs locally at `http://127.0.0.1:8000` with admin accessible. Phase 1 (Render free-tier deployment) is in progress — `render.yaml` and settings fixes are done; the app has not yet been deployed to Render. Documentation files (PRD, Architecture, Rules, Phases, design, memory) created 2026-07-25.

---

## Recently Completed Tasks

| Date | Task |
|---|---|
| 2026-07-24 | Fixed BOM encoding in 44 Python files |
| 2026-07-24 | Fixed missing `__init__.py` files in 12 packages |
| 2026-07-24 | Fixed `STATICFILES_STORAGE` → `STORAGES` dict (Django 5 API) |
| 2026-07-24 | Fixed `navbar.html` include path (`includes/navbar.html`) in `base.html` |
| 2026-07-24 | Removed committed `cert.crt` / `cert.key` from git tracking |
| 2026-07-25 | Created PRD.md, Architecture.md, Rules.md, Phases.md, design.md, memory.md |

---

## Active Work Items

| File / Feature | Status | Notes |
|---|---|---|
| Render deployment | In progress | `render.yaml` ready; env vars not yet set in Render dashboard |
| `templates/base.html` | Pending fix | `{% include 'navbar.html' %}` → `{% include 'includes/navbar.html' %}` not yet applied |

---

## Known Issues & Blockers

| Issue | Severity | Notes |
|---|---|---|
| `navbar.html` include path wrong in `base.html` | High | Home page returns 500; fix: change to `includes/navbar.html` |
| Render free PostgreSQL expires 90 days after creation | Medium | Must migrate before ~2026-10-24 |
| PDF media files are ephemeral on Render free tier | Medium | Lost on every redeploy; fix in Phase 3 (S3/R2) |
| In-process job queue lost on dyno restart | Low | Acceptable for MVP; migrate to Celery/Redis in Phase 3 |
| `cert.crt` / `cert.key` still in git history | Low | Throwaway self-signed dev certs — rotate if real |

---

## Next Immediate Steps

1. Fix `base.html` navbar include: `{% include 'includes/navbar.html' %}`
2. Verify home page loads without 500 error
3. Create Render account at https://render.com
4. Create new Web Service → connect GitHub repo
5. Add PostgreSQL free tier database in Render dashboard
6. Set environment variables in Render: `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS`, `DATABASE_URL`, `GROQ_API_KEY`, `TAVILY_API_KEY`, `GOOGLE_API_KEY`, `CSRF_TRUSTED_ORIGINS`
7. Trigger deploy and verify `/health/` returns `{"status": "ok"}`
8. Test end-to-end: register → submit query → download PDF
9. After deploy confirmed: write README with screenshot and push to GitHub
10. Publish LinkedIn post with live URL

---

## Pending Decisions

| Question | Context | Needed by |
|---|---|---|
| Use Cloudflare R2 or AWS S3 for PDF storage? | R2 is free 10 GB/month; S3 requires card | Phase 3 start |
| Use Upstash Redis (free) or Render Redis (paid) for Celery? | Upstash has free tier; Render Redis requires paid plan | Phase 3 start |
| Should premium tier require Stripe payment integration? | Currently no billing logic exists | Phase 3/4 |
| Make reports publicly shareable via link? | Would require token-based auth on PDF download | Phase 2 |

---

## Environment State

- **Local:** `myenv` virtualenv active; SQLite DB at `db.sqlite3`; `DEBUG=True` in `.env`
- **Required `.env` values:** `SECRET_KEY`, `GROQ_API_KEY`, `TAVILY_API_KEY`, `GOOGLE_API_KEY`
- **After any `git pull`:** run `python manage.py migrate` if new migrations present
- **Branch:** `main` (no feature branches active)

---

## Recent Learnings & Gotchas

- Django 5.0 removed `STATICFILES_STORAGE` — must use `STORAGES` dict with `staticfiles` key
- Template `{% include %}` paths are relative to the `TEMPLATES[0]['DIRS']` root (`templates/`), so `includes/navbar.html` not `navbar.html`
- Windows UTF-8-with-BOM encoding adds `﻿` to Python files — causes `SyntaxError` on import; strip with `fix_bom.py`
- Render free web service spins down after 15 min inactivity — first request after sleep takes ~30 s
- Render free PostgreSQL has a hard 90-day expiry — data is deleted, not just paused
- `createsuperuser` fails with `UNIQUE constraint failed: accounts_user.email` if email already exists — use a different email or promote existing user via shell

---

## Testing Status

- No automated tests written yet
- Manual testing: admin panel works, runserver starts cleanly
- Home page: currently returns 500 due to `navbar.html` include path bug (unfixed)
- Research pipeline: not yet tested end-to-end locally (requires valid API keys in `.env`)

---

## Deployment Log

| Date | Environment | Version | Notes |
|---|---|---|---|
| — | Production (Render) | — | Not yet deployed |
| 2026-07-24 | Local | HEAD | Server runs; admin works; home page 500 (navbar bug) |
