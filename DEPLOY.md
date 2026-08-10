# Deploy AI Research Agent to Render (Free Tier)

> Roadmap status: Phases 0–4 are code-complete. This guide takes you from repo → live URL and then through the Phase 3 opt-in services.

## Prerequisites

1. **GitHub account** — https://github.com
2. **Render account** — https://render.com (sign in with GitHub)
3. **API keys**
   - Groq: https://console.groq.com
   - Tavily: https://tavily.com
   - Google (optional, Gemini fallback): https://makersuite.google.com

---

## Phase 1 — Deploy (code-ready, ~10 min)

The repo ships `render.yaml` + `build.sh`, so this is a one-click Blueprint.

1. Push the repo to GitHub (make sure `.env` is **not** committed — it's git-ignored).
2. Render Dashboard → **New → Blueprint** → select the repo.
3. Render provisions:
   - web service `ai-research-agent` (free)
   - Postgres `ai-research-agent-db` (free, expires after 90 days — set a backup reminder)
4. In the web service **Environment** tab, fill in the secrets `sync=false` entries from `render.yaml`:
   - `GROQ_API_KEY`, `TAVILY_API_KEY`, `GOOGLE_API_KEY`
   - `ALLOWED_HOSTS` is pinned to `ai-research-agent.onrender.com` — change it if you rename the service.
5. Deploy. `build.sh` runs `pip install -r requirements.txt` → `python manage.py migrate` → `python manage.py collectstatic`.
6. Verify: `https://<app>.onrender.com/health/` → `{"status": "ok"}`.

### Definition of Done (test on the live URL)

- [ ] App accessible at `https://<app>.onrender.com` (no 500 on home)
- [ ] Register → login → submit a research query → watch SSE progress
- [ ] PDF download works
- [ ] `/health/` returns `{"status": "ok"}`

### Free-tier notes

- Web service spins down after ~15 min idle → first request cold-starts in ~30 s.
- PDFs in `media/` are **ephemeral** — regenerate or move to R2 (below).
- Run backups with `scripts/backup.sh` before the 90-day Postgres expiry.

---

## Phase 2 — Launch (no code)

- README, LICENSE (MIT), CONTRIBUTING, `.github/` issue templates: ✅ in repo.
- LinkedIn post draft: `.github/LINKEDIN_POST_DRAFT.md` — add screenshots (`docs/screenshots/`), paste, publish.
- Set repo topics: `django`, `llm`, `groq`, `ai-agent`, `research`, `python`.

---

## Phase 3 — Production hardening (all opt-in via env vars)

Already coded; flip them when you provision the services:

| Feature | Env vars | Provision |
|---|---|---|
| Celery job queue | `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`; install `celery[redis]` | Upstash Redis free tier; add a `celery -A config worker` background service in render.yaml |
| Persistent media (R2/S3) | `USE_S3_MEDIA=True`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET`, `R2_ENDPOINT_URL`; install `django-storages[s3]` | Cloudflare R2 (10 GB free) |
| Error tracking | `SENTRY_DSN`, optional `SENTRY_TRACES_RATE` | Sentry free tier (already in requirements) |
| Real email (verification + password reset) | `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_BACKEND` | Any SMTP (Gmail app password, Brevo, Mailgun) |

Deployed Celery worker `render.yaml` snippet:

```yaml
  - type: worker
    name: ai-research-agent-worker
    runtime: python
    plan: free
    buildCommand: "./build.sh"
    startCommand: "celery -A config worker --loglevel=info"
    envVars:
      - key: CELERY_BROKER_URL
        sync: false
```

---

## Phase 4 — Feature flags (already in code)

Off-by-default experiments, toggle in the environment:

```bash
FEATURE_COLLAB_V2=True    # collaboration v2 UI
FEATURE_ADMIN_API=True    # admin analytics endpoints
```

Core P1/P2 features (templates, share links, rating, quota chip, LLM/depth toggles) ship ON.

---

## Rollback / troubleshooting

- **Boot crash on Render** → check `DATABASE_URL` is linked; `dj-database-url` is in requirements.
- **Static files 404** → confirm `collectstatic` ran in the build log (`DISABLE_COLLECTSTATIC` was removed).
- **CSRF errors** → `CSRF_TRUSTED_ORIGINS` must match your exact `https://` hostname.
- **500 with no logs** → set `SENTRY_DSN` and re-deploy; the exception will appear in Sentry.
