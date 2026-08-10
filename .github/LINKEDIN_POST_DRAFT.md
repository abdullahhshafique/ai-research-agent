# LinkedIn Post Draft — AI Research Agent (Phase 2)

> Publish on your LinkedIn — replace `<LIVE_URL>` and `<GH_URL>` with the actual links, attach the `docs/screenshots/` images, and paste.

---

🚀 I just open-sourced **AI Research Agent** — a full-stack Django app that turns a single question into a structured, cited, downloadable PDF research report, automatically.

### The problem
Researchers and students spend hours manually searching, reading, and synthesising sources. Existing tools either return raw search results (you do the synthesis) or lock the good features behind a paywall.

### What it does
Search → summarise → report → PDF, all in one pipeline:

* 🔍 **Web research** via the Tavily API with cached results
* 🧠 **AI summarisation** on Groq (Llama 3.3 70B) with a Gemini fallback
* 📄 **Branded PDF export** using fpdf2 (Unicode-aware cover page, per-user logos)
* ⚡ **Live progress** via Server-Sent Events — you watch each stage complete
* 📚 **History, templates, share-links, quotas, and an admin dashboard** built-in

Built on Django 5, it runs on Render's free tier, in Docker, or on Fly.io. I documented the 5-phase roadmap — from local MVP to production-grade (Sentry, Celery, R2) — in the repo.

### Tech stack
`Django 5 · Python 3.12 · Tailwind · Server-Sent Events · Groq / Gemini · Tavily · fpdf2 · PostgreSQL / SQLite · Gunicorn · WhiteNoise · Docker · Render / Fly.io`

**Live demo:** `<LIVE_URL>`
**GitHub:** `<GH_URL>`

I'd love your feedback, issues, and stars — and I'm happy to walk through the architecture if you're curious.

#Django #Python #AI #LLM #OpenSource #FullStack #DevTools

---

### Suggested screenshots (`docs/screenshots/`)
1. `home.png` — landing page
2. `submit.png` — query form
3. `progress.png` — SSE progress mid-run
4. `report.png` — rendered Markdown preview
5. `pdf.png` — branded PDF cover
