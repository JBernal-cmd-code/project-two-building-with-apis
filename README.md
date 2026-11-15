# project-two-building-with-apis

A book tracker built on the [Open Library API](https://openlibrary.org/developers/api).
See [docs/research/external-api-options.md](docs/research/external-api-options.md)
for why Open Library was chosen.

## Setup

Requires [uv](https://docs.astral.sh/uv/). uv installs Python 3.14 and all
packages for you.

```bash
uv sync
cp .env.example .env    # then put your email in .env
```

`CONTACT_EMAIL` in `.env` is sent in the `User-Agent` header, as Open Library
asks. It is optional: without it the script prints a warning and still works.
`.env` is ignored by git.

## Running the web app (MyChapterCollection)

```bash
uv run python manage.py migrate
uv run python manage.py tailwind build   # first run downloads the Tailwind binary
uv run python manage.py runserver
```

Then open <http://127.0.0.1:8000/>. Use `uv run python manage.py tailwind runserver`
instead to rebuild the CSS automatically while editing templates.

Styling is Tailwind CSS + DaisyUI through `django-tailwind-cli`. With
`TAILWIND_CLI_USE_DAISY_UI = True` it downloads the standalone
`tailwindcss-extra` binary (DaisyUI bundled) into `.django_tailwind_cli/`, so no
Node.js or npm is needed. The theme lives in `styles/source.css`; the built
`static/css/tailwind.css` is committed so the app is styled right after cloning.
HTMX is a pinned local file at `static/js/htmx.min.js` (v2.0.4).

`DJANGO_SECRET_KEY` can be set in `.env`; a development-only key is used otherwise.

### Demo data

```bash
uv run python manage.py seed_demo
```

This creates (or reuses) a `demo` user and about 25 saved books across all four
statuses, then prints the demo password. Log in with it to see the collection
right away. The book data is built into the command (real Open Library work
keys, cover IDs, and page counts), so it works offline. A few books
deliberately have no cover, which shows the placeholder. Running it again skips
books the demo user already has.

**The demo password is for local development only.** It is printed by the
command and written in its source, so never use it, or the demo account, on a
deployed site.

### REST API

The app has its own API for saved books. It never calls Open Library. Every
request must be authenticated (unauthenticated requests get `401`), and each
user sees only their own books (another user's book is a `404`).

| Method | URL | Purpose |
|---|---|---|
| `POST` | `/api/token/` | Get your token from `username` and `password` |
| `GET` | `/api/books/` | List your books (20 per page, with `count`, `next`, `previous`) |
| `POST` | `/api/books/` | Save a book: `ol_work_key` and `title`, plus optional `authors`, `first_publish_year`, `cover_id`, `total_pages` |
| `GET` | `/api/books/<id>/` | One book |
| `PUT` / `PATCH` | `/api/books/<id>/` | Update `status`, `current_page`, `total_pages`, `rating`, `notes` |
| `DELETE` | `/api/books/<id>/` | Remove a book |

The list takes the same parameters as My Collection: `q` (title or author),
`status` (`want_to_read`, `reading`, `finished`, `abandoned`), `min_rating`
(1–5), `ordering` (`-created_at`, `-updated_at`, `title`, `authors`,
`-rating`, `-first_publish_year`), and `page`. Book facts (work key, title,
authors, year, cover ID) are locked after creation, and changes to them in an
update are ignored.

```bash
curl -X POST http://127.0.0.1:8000/api/token/ -d "username=demo" -d "password=<demo password>"
curl -H "Authorization: Token <token>" "http://127.0.0.1:8000/api/books/?status=reading&ordering=title"
```

On Windows PowerShell, type `curl.exe` instead of `curl`. In PowerShell,
`curl` is an alias for `Invoke-WebRequest`, which doesn't accept these options.

While logged in on the website, you can also open `/api/books/` in the browser
to use DRF's browsable API.

## Scripts

### `scripts/search_books.py`: search Open Library from the console

```bash
uv run scripts/search_books.py
```

Type a search (title, author, or anything) to see the first 10 matches. Press
Enter on an empty line or type `q` to quit. Ctrl+C also exits.

Every request uses a 10-second timeout. If nothing matches, or if the request
fails (timeout, no connection, an HTTP error such as 503 or 429, or an
unreadable response), the script prints a short message and asks for the next
search instead of crashing.

## Tests and code quality

```bash
uv run pytest            # offline tests, no network calls
uv run ruff check .      # lint
uv run ruff format .     # format
```

The tests replace `requests.get` with fakes, so they check the no-results and
failure messages without touching the network. An autouse fixture in
`tests/conftest.py` blocks sockets, so any test that forgets to fake a request
fails with "Network access is blocked in tests".

### Manual checklist for `search_books.py`

| Step | Expected |
|---|---|
| Run with no `.env` file | Warning explains how to create `.env`, then searching works |
| Search `the hobbit` | "Found N results" header and a numbered list of 10 books |
| Search `zzqxvwplm` | "No books matched" message, then the prompt again |
| Turn off Wi-Fi, search anything | "Could not connect to Open Library" message, then the prompt again |
| Turn Wi-Fi back on, search again | Results appear (the script recovered) |
| Press Enter on an empty line, or type `q` | "Goodbye!" and the script exits |
