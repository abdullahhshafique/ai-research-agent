# Contributing to AI Research Agent

Thanks for your interest! The fastest way to contribute is:

1. **Fork & clone** the repo.
2. **Set up** with `pip install -r requirements.txt`, `python manage.py migrate`, `python manage.py runserver`.
3. **Run the tests** with `python run_tests.py` and keep them green.
4. **Format/lint** to match the existing code style — read `Rules.md` for the project's rules (Django conventions, security headers, no raw secrets, etc.).
5. **Open a Pull Request** with a clear description and, for bug-fixes, a minimal reproduction.

Please:

- Never commit `.env` or any API keys — `.env.example` is the reference.
- Add tests for new views/services under `apps/<app>/tests.py`.
- Keep templates in `templates/pages/` and URL names namespaced.
- Don't introduce new top-level `utils/` packages — use `apps/utils/`.

For anything non-trivial (new app, new dependency, schema change), open an issue first so we can discuss the approach.
