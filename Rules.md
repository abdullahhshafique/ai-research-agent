# Rules — AI Research Agent

## Coding Standards

- **Language:** Python 3.12
- **Style:** PEP 8; max line length 100 characters
- **Naming:** `snake_case` for variables/functions/modules; `PascalCase` for classes; `UPPER_SNAKE` for constants
- **Functions:** Single responsibility; max ~40 lines; extract helpers rather than nesting
- **Comments:** Prefer self-documenting code; add a docstring to every class and public method; inline comments only for non-obvious logic
- **No magic numbers:** Name constants at module level
- **Imports:** stdlib → third-party → local, separated by blank lines; no wildcard imports

---

## Commit & Branching Convention

- **Branch naming:** `feature/<short-description>`, `fix/<short-description>`, `chore/<short-description>`
- **Commit format:** Conventional Commits
  ```
  feat: add PDF download endpoint
  fix: handle empty Tavily results gracefully
  chore: update requirements.txt
  docs: add Architecture.md
  ```
- **Main branch:** `main` is always deployable
- **No direct pushes to main** — use PRs (even solo; self-review is fine)
- **Squash merge** feature branches to keep history clean

---

## Documentation Standards

- Public classes and methods: Google-style docstrings
- Complex algorithms: inline block comment above the logic
- External API integrations: comment the API endpoint and key parameters being used
- `README.md`: keep setup instructions current after any env var or dependency change
- Update `memory.md` at the end of every working session

---

## Dependency Management

- Add packages to `requirements.txt` with a minimum version pin (`>=x.y`)
- Before adding a new package: check it is actively maintained, has a permissive licence (MIT/Apache/BSD), and is not replaceable with stdlib
- No packages that duplicate stdlib functionality (e.g. no `requests` when `urllib` suffices — this project already enforces this)
- Run `pip audit` before deploying to check for known vulnerabilities
- Do not pin to exact versions in `requirements.txt` unless a breaking change is known; exact pins go in a `requirements.lock` if needed

---

## Error Handling Patterns

- **Service layer:** raise typed exceptions (`SearchError`, `SummarisationError`) rather than returning `None` or bare strings
- **Views:** catch service exceptions, set `ResearchQuery.status = failed`, store `error_message`, return appropriate HTTP status
- **Never swallow exceptions silently** — at minimum log at `ERROR` level
- **LLM calls:** always wrap in try/except; implement the Groq → Gemini fallback chain
- **User-facing errors:** plain English messages; never expose stack traces or API keys
- **HTTP client:** check response status codes explicitly; raise on non-2xx

---

## Logging & Observability Rules

- Use Django's standard `logging` module; configure in `settings.py`
- Log levels: `DEBUG` for pipeline step entry/exit (dev only), `INFO` for pipeline completion, `WARNING` for quota hits and rate limits, `ERROR` for exceptions
- **Never log PII** — no email addresses, usernames, or query text in log lines
- Always include `query_id` in pipeline log messages for traceability
- Structured log format in production: `%(levelname)s %(asctime)s %(name)s %(message)s`

---

## Testing Rules

- Every service function must have at least one unit test
- Mock all external I/O (Tavily, Groq, Gemini, filesystem) in unit tests
- Test file naming: `test_<module>.py` inside `apps/<app>/tests/`
- Test function naming: `test_<what>_<condition>_<expected>`
- Do not test Django internals (ORM, auth) — test your own logic
- Minimum coverage target: 80% on `apps/research/services/`

---

## Accessibility Rules

- All pages must pass WCAG 2.1 AA
- Use semantic HTML (`<nav>`, `<main>`, `<article>`, `<button>` not `<div onclick>`)
- Every `<img>` must have a meaningful `alt` attribute
- Colour contrast ratio ≥ 4.5:1 for normal text, ≥ 3:1 for large text
- All interactive elements must be keyboard-navigable (visible focus ring)
- Form inputs must have associated `<label>` elements
- Progress bar must have `role="progressbar"` with `aria-valuenow`

---

## Performance Rules

- Page load target: < 2 s (HTML + critical CSS)
- Avoid N+1 queries — use `select_related` / `prefetch_related` on history/dashboard views
- Paginate history list (default 20 items per page)
- Static files served by WhiteNoise with compression and long-lived cache headers
- Do not load unused JS/CSS on every page

---

## Security Rules

- **Never commit secrets** — `.env` is in `.gitignore`; use `.env.example` for documentation
- API keys passed via HTTP headers only, never URL query parameters
- `SECRET_KEY` must be a random 50+ character string in production
- `DEBUG=False` in production — enforced via env var
- `ALLOWED_HOSTS` must be explicitly set in production
- CSRF protection enabled on all POST endpoints — never exempt research/auth views
- File uploads (if added): validate MIME type and size server-side; store outside `MEDIA_ROOT` accessible to web
- Rotate API keys immediately if accidentally committed

---

## AI Assistance Boundaries

- AI may suggest code, refactors, and documentation
- AI must not modify `config/settings.py` production values or `.env` files
- AI-generated code must always include error handling — no bare `except:` blocks
- AI must not invent API endpoints or model fields that don't exist
- AI must not remove existing test cases
- AI-generated migrations must be reviewed before applying to production DB
- AI may not bypass quota or rate-limit middleware

---

## Code Review Checklist

Before merging any PR, verify:

- [ ] No secrets or credentials in code or commit history
- [ ] All new service functions have unit tests
- [ ] Error handling present for all external API calls
- [ ] No N+1 DB queries introduced
- [ ] `query_id` included in any new log messages
- [ ] New env vars documented in `.env.example`
- [ ] `requirements.txt` updated if new packages added
- [ ] Migrations included if models changed
- [ ] Accessibility: semantic HTML, labels, alt text
- [ ] `memory.md` updated if architecture or scope changed

---

## Environment-Specific Behaviour

| Setting | Local dev | Production |
|---|---|---|
| `DEBUG` | `True` | `False` |
| Database | SQLite | PostgreSQL (via `DATABASE_URL`) |
| Static files | Django dev server | WhiteNoise |
| Media files | Local `media/` | Local `media/` (ephemeral — migrate to S3 later) |
| HTTPS | No | Yes (`SECURE_SSL_REDIRECT=True`) |
| Log level | `DEBUG` | `INFO` |
| Search cache | File-based (`/tmp/`) | File-based (`/tmp/`) |
