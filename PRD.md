# Product Requirements Document — AI Research Agent

## Problem Statement & Context

Researchers, students, and professionals spend hours manually searching, reading, and synthesising information from multiple web sources. Existing tools either return raw search results (requiring manual synthesis) or are expensive AI products. This project automates the full pipeline — search → summarise → report → PDF — in one free-to-use web app. The timing is right because capable open-weight LLMs (Llama 3.3 via Groq) are now fast and free at meaningful scale.

---

## Success Metrics / KPIs

| Metric | Target |
|---|---|
| Research pipeline completion rate | ≥ 95% of submitted queries complete without error |
| Pipeline end-to-end time | ≤ 60 s for a standard 5-source query |
| PDF export success rate | ≥ 99% |
| User quota utilisation | Free users hit quota limit < 20% of sessions (indicates value without abuse) |
| Daily active users (post-launch) | 50 DAU within 30 days |
| Report quality (user rating) | ≥ 4/5 average if rating feature added |

---

## Personas

### Persona 1 — The Busy Professional (Primary)
- **Name:** Sarah, 34, marketing manager
- **Goal:** Quickly understand a new market or competitor without spending hours reading
- **Frustration:** Search engines return 10 blue links; she has to open each one and read manually
- **Context:** Uses a laptop at work, needs a shareable PDF for her team

### Persona 2 — The Student Researcher
- **Name:** Ali, 22, university student
- **Goal:** Gather and summarise sources for an essay or presentation
- **Frustration:** Academic databases are paywalled; free tools give shallow results
- **Context:** Uses the app on a laptop, needs citations and structured output

### Persona 3 — The Developer / Power User
- **Name:** Dev, 28, software engineer
- **Goal:** Quickly research a technical topic (library, API, architecture pattern)
- **Frustration:** Stack Overflow threads are fragmented; wants a synthesised answer
- **Context:** Comfortable with technical interfaces, may use the API directly

---

## User Stories

### P0 — Must Have (MVP)
- As a user, I want to submit a natural-language research query so that the system searches the web for me.
- As a user, I want to see real-time progress so that I know the research is running.
- As a user, I want a structured Markdown report with a summary, key insights, and sources so that I can read the findings quickly.
- As a user, I want to download the report as a PDF so that I can share it.
- As a user, I want to register and log in so that my research history is saved.

### P1 — Should Have
- As a user, I want to retry a failed query so that I don't lose my work.
- As a user, I want to view my research history so that I can revisit past reports.
- As a user, I want to save a query as a template so that I can reuse common research patterns.
- As a user, I want to see my remaining quota so that I know how many queries I have left.

### P2 — Nice to Have
- As a user, I want to collaborate on a research query with a teammate.
- As a user, I want to choose between basic and advanced search depth.
- As a user, I want to choose the LLM (Groq or Gemini) for my query.
- As an admin, I want a dashboard to view API key usage and logs.

---

## Scope

### In Scope (MVP)
- User registration, login, logout
- Research query submission with real-time SSE progress
- Web search via Tavily API
- LLM summarisation via Groq (Llama 3.3 70B), Gemini fallback
- Markdown report generation
- PDF export (fpdf2)
- Research history
- Query versioning (retry creates new version)
- Hourly quota enforcement (10 free / 100 premium)
- Admin dashboard

### Out of Scope (Future)
- Mobile app
- Real-time collaboration editing
- Custom LLM fine-tuning
- Billing / payment integration
- Public API with API keys for third-party developers
- Multi-language report output

---

## Functional Requirements

### Authentication
- Users register with username + unique email + password
- Django's built-in auth; custom User model with unique email constraint
- Login redirects to home; logout clears session
- Password validation enforced (length, similarity)

### Research Pipeline
- Query text: 10–2000 characters, required
- Search depth: `basic` or `advanced` (default: advanced)
- Max results: 1–10 (default: 5)
- LLM choice: `groq` or `gemini` (default: groq)
- Pipeline runs in a background worker thread
- SSE endpoint streams progress events: `status` (0–100%), `complete`, `error`
- On error: status set to `failed`, error message stored, user can retry
- Retry creates a new `ResearchQuery` linked via `parent_query`; `is_latest` updated

### Quota
- Free users: 10 queries/hour; Premium: 100/hour
- Quota resets every hour from first use
- Quota exceeded returns HTTP 429 with reset time

### Reports
- PDF saved to `media/reports/`
- `GeneratedReport` record created on completion
- PDF downloadable via authenticated URL

### Edge Cases
- Empty Tavily results → pipeline fails with clear error message
- LLM API timeout → retry with Gemini fallback; if both fail → `failed` status
- Text > 60 KB → chunked (4 000 tokens, 200-token overlap), per-chunk summaries merged
- Concurrent queries from same user allowed up to quota limit

---

## Non-Functional Requirements

| Requirement | Target |
|---|---|
| Page load (home/history) | < 2 s |
| Pipeline completion | ≤ 60 s (standard query) |
| Availability | 99% uptime (Render free tier best-effort) |
| Security | HTTPS enforced in prod; CSP headers; HSTS; secure cookies |
| Accessibility | WCAG 2.1 AA for all public-facing pages |
| Browser support | Chrome 110+, Firefox 110+, Safari 16+, Edge 110+ |
| Mobile | Responsive layout, usable on 375 px viewport |
| Scalability | Single-server MVP; stateless design allows horizontal scaling later |

---

## User Flow Summaries

1. **Register → Login → Home**
2. **Home → Submit Query → Progress Stream → Report View → Download PDF**
3. **History → Select Past Query → View Report / Retry**
4. **Templates → Select Template → Pre-fill Query Form → Submit**

---

## Assumptions & Dependencies

- Tavily API free tier is sufficient for MVP traffic
- Groq free tier provides adequate rate limits for 10 queries/user/hour
- Render free tier (512 MB RAM, spun down after inactivity) is acceptable for MVP
- PostgreSQL provided by Render free tier (90-day limit — must migrate before expiry)
- Google Gemini API free tier available as fallback

---

## Open Questions

| Question | Owner | Deadline |
|---|---|---|
| Should premium tier require payment integration? | Product | Before Phase 3 |
| What happens when Render free PostgreSQL expires (90 days)? | Dev | Before go-live |
| Should reports be publicly shareable via link? | Product | Phase 2 |

---

## Glossary

| Term | Definition |
|---|---|
| Pipeline | The end-to-end process: search → chunk → summarise → report → PDF |
| SSE | Server-Sent Events — one-way HTTP stream from server to browser |
| Quota | Maximum number of research queries a user can submit per hour |
| Chunking | Splitting large text into overlapping segments for LLM processing |
| Version | A new `ResearchQuery` created when a user retries an existing query |
| Groq | LLM inference provider hosting Llama 3.3 70B |
| Tavily | Web search API optimised for AI agents |
