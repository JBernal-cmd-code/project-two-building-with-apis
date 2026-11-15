# MyChapterCollection

A private, per-user reading tracker built with Django that finds books through the Open Library API.

## Stack

- Python, managed with **uv** (package manager and runner)
- Django with a SQLite database
- Django REST Framework (session + token auth)
- Tailwind CSS + DaisyUI via `django-tailwind-cli` (standalone executable, no Node/npm)
- HTMX, served as a pinned local static file (no CDN)
- pytest + pytest-django

## Commands

- `uv run python manage.py migrate`: apply database migrations
- `uv run python manage.py seed_demo`: create the `demo` user and ~25 saved books (offline, safe to rerun)
- `uv run python manage.py runserver`: start the dev server at http://127.0.0.1:8000/
- `uv run python manage.py tailwind build`: build `static/css/tailwind.css` from `styles/source.css` (rebuild and commit after template class changes)
- `uv run pytest`: run the full offline test suite, including the script tests
- `uv run ruff check .` and `uv run ruff format .`: lint and format

## Architecture decisions (from the PRD)

- Book facts are copied into one local `SavedBook` row per user per book; there is no shared catalog table.
- Open Library is called only by the search page. Collection, detail, save, and the API never call it, so they keep working during an outage.
- Privacy comes from owner-scoped queries: every website and API query starts from the current user's books, and other users' books return 404.
- Validation rules live in the model so the website and API behave the same.
- Book facts are locked after creation; only reading-tracking fields are editable.
- Tests run offline: Open Library is faked with monkeypatch, and any unfaked network call fails.
- `scripts/search_books.py` and its tests stay unchanged and must keep passing.

## References

- PRD: `prd/mychaptercollection.md`
- Implementation plan: `plans/mychaptercollection.md`
- Collection layout prototype (Variant D is the visual reference): `prototypes/collection-layouts.html`
- API choice research: `docs/research/external-api-options.md`
