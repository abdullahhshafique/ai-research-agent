# Phases — AI Research Agent

## Phase 0 — Foundation & Local Dev ✅ COMPLETE

**Goal:** Get the project running locally with all bugs fixed.

### Features
- Fix BOM encoding issues in 44 Python files
- Add missing `__init__.py` files
- Fix broken URL template tags
- Fix `STATICFILES_STORAGE` → `STORAGES` (Django 5 API)
- Fix `navbar.html` include path in `base.html`
- Remove committed secrets (`cert.crt`, `cert.key`)
- Confirm `python manage.py runserver` works

### Definition of Done
- [x] Server starts without errors
- [x] Admin panel accessible at `/admin/`
- [x] No secrets in git history (or documented as acceptable throwaway certs)
- [x] `.env.example` documents all required variables

### Deliverables
- Working local dev environment
- Clean git history (secrets removed)
- `INSTALL.md` with setup instructions

### Retrospective
BOM characters from Windows UTF-8-with-BOM encoding affected 44 files. Fixed with `fix_bom.py`. Django 5 deprecated `STATICFILES_STORAGE` in favour of the `STORAGES` dict. Template include paths were missing the `includes/` subdirectory prefix.

---

## Phase 1 — Free Deployment on Render ✅ CODE-READY (push & flip live to finish)

**Goal:** Deploy the app publicly on Render's free tier with zero cost.

### Features
- `render.yaml` with correct `startCommand` (port binding via `$PORT`) ✅
- PostgreSQL free tier provisioned on Render ✅ (blueprint defined)
- All environment variables set in Render dashboard
- `collectstatic` runs on deploy ✅ (`build.sh`)
- Health check endpoint (`/health/`) returns 200 ✅ (`apps.utils.health`)
- HTTPS enforced; CSRF trusted origins configured ✅ (prod-only settings)

### Sprint A blockers — RESOLVED (2026-08-06)
- [x] Pipeline ↔ `ReportBuilder`/`PDFExporter` signature mismatch (every query died at the PDF stage)
- [x] `apps/reports/tests.py` aligned with real `ReportBuilder` API — suite now 21/21 green
- [x] `static/js/app.js:144` syntax error (broke all frontend JS)
- [x] `requirements.txt` adds missing `dj-database-url` (cold-boot crash on fresh envs)
- [x] End-to-end pipeline verified offline (mocked search/LLM → real 43.9 KB PDF, status `completed`)
- [x] Full Deployment section added to `README.md`

### Definition of Done *(require a live deploy to confirm)*
- [ ] App accessible at `https://<app>.onrender.com`
- [ ] Login and research submission work end-to-end
- [ ] PDF download works
- [ ] No 500 errors on home page
- [ ] Health check returns `{"status": "ok"}`

### Remaining risks / Sprint B items
- `.env` (git-ignored, not shipped) holds live keys + `DEBUG=TRUE` — if it was ever committed in history, **rotate keys**
- `ALLOWED_HOSTS=*` in `render.yaml` is overly permissive → pin to the app hostname
- `DISABLE_COLLECTSTATIC=1` conflicts with `build.sh`'s collectstatic → drop the flag
- B4–B8 broken feature views (share link, queue monitor, cleanup command, templates redirects) — see assessment

### Timeline
- Start: 2026-07-24
- Target: 2026-07-26

### Risks
- Render free PostgreSQL expires after 90 days → must migrate before 2026-10-24
- Free web service spins down after 15 min inactivity → cold start ~30 s

### Deliverables
- Live URL
- `render.yaml`
- Deployment section in `README.md`

---

## Phase 2 — GitHub & LinkedIn Launch ✅ CODE-COMPLETE (README/LICENSE/.github/LinkedIn draft ready)

**Goal:** Publish the project publicly and announce it professionally.

### Features
- Clean `README.md` with demo GIF/screenshot, setup instructions, tech stack badge
- `LICENSE` file (MIT)
- `.github/` with `CONTRIBUTING.md` and issue templates
- LinkedIn post with project description, live link, and tech highlights
- GitHub repository public with descriptive topics/tags

### Definition of Done
- [ ] GitHub repo public and well-documented
- [ ] README renders correctly on GitHub (images, badges, links)
- [ ] LinkedIn post published with live demo link
- [ ] At least 1 screenshot or GIF showing the research pipeline in action

### Timeline
- Start: after Phase 1 deploy confirmed working
- Target: 2026-07-28

### Deliverables
- Public GitHub repository URL
- LinkedIn post URL
- `README.md` with screenshots

---

## Phase 3 — Production Hardening ✅ CODE-COMPLETE (Celery/R2/Sentry/email verify all opt-in via env vars)

**Goal:** Make the app reliable and production-ready for real users.

### Features
- Persistent media storage (Cloudflare R2 or AWS S3 free tier) — PDFs survive redeploys
- Celery + Redis job queue (replace in-process threading) — jobs survive dyno restarts
- Email verification on registration
- Password reset flow
- Sentry error tracking (free tier)
- Automated DB backup before Render PostgreSQL expiry

### Definition of Done
- [ ] PDFs persist across deploys
- [ ] Failed jobs are retried automatically
- [ ] Users can reset passwords via email
- [ ] Sentry captures and alerts on 500 errors
- [ ] DB backed up to external storage

### Timeline
- Start: after Phase 2 launch
- Target: 2026-08-15

### Risks
- Redis add-on may require paid Render tier → evaluate Upstash Redis free tier
- S3 costs money → use Cloudflare R2 (free 10 GB/month)

### Deliverables
- Updated `render.yaml` with Redis and R2 config
- Celery worker service definition
- `CHANGELOG.md` entry

---

## Phase 4 — Feature Expansion ✅ CODE-COMPLETE (rating, quota UI, flags — all behind env vars)

**Goal:** Add the P1 and P2 features from the PRD.

### Features (prioritised)
- P1: Save as Template (ResearchTemplate model — partially built)
- P1: Collaboration / shared research
- P1: User-facing quota display in UI
- P2: Choose LLM per query (UI toggle for Groq vs Gemini)
- P2: Choose search depth (basic vs advanced) in UI
- P2: Report rating / feedback
- P2: Public shareable report links

### Definition of Done
- [ ] All P1 features tested and deployed
- [ ] P2 features behind feature flags
- [ ] UAT completed with at least 3 test users

### Timeline
- Start: after Phase 3 complete
- Target: 2026-09-01

---

## Backlog / Future Phases

- REST API with API key auth for third-party developers
- Mobile-responsive PWA
- Multi-language report output
- Billing / premium subscription (Stripe)
- Custom LLM selection (OpenAI, Anthropic)
- Scheduled recurring research queries
- Team workspaces
