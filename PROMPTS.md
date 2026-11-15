# PROMPTS.md — AI Usage Log

This file is the record of AI use on this codebase. At the end of every
agent session, direct the agent to write the session log with this prompt:

> Append a session log to PROMPTS.md at the repo root, under today's date,
> newest entry at the top. Record every prompt I gave you this session, in
> order, including any corrections. End the entry with a short summary:
> the outcome, any places where I deviated from a recommended answer or
> asked follow-up questions, and anything that went sideways.

Two rules:

- Entries are added only by that prompt, never unprompted.
- New entries go at the top. Never rewrite or delete an old entry — the
  log is part of your work, and an honest log of a session that went
  sideways is worth more than a tidy one.

Each entry has this shape:

    ## YYYY-MM-DD — <one-line summary>

    ### Prompts
    1. ...

    ### Summary
    - **Outcome:** what was built and what was kept
    - **Deviations:** recommendations overridden, follow-up questions asked
    - **Sideways:** failures, wrong turns, and how they were caught

## 2026-11-15 — Phase 5: Collection search, filters, sort, pagination, and HTMX updates

### Prompts
1. `/implement @prd/mychaptercollection.md @plans/mychaptercollection.md
   implement Phase 5. Show me the TDD candidates to approve first, then go
   through RED and GREEN without stopping unless something unexpected happens.`
2. Approved, all three. Make sure the normal tests also cover that changing a
   filter or search goes back to page 1.
3. Verified in the browser. Layout, status filter, counts updating with
   search and rating, sorting with unrated last, pagination keeping my sort,
   back button, bad URLs, empty state, and offline all work. One usability
   fix: when I clear the search box by clicking the X or deleting all the
   text, I have to press Enter again to see my full collection. Make clearing
   the search box update the collection right away. Typing a new search should
   still wait for Enter.
4. The clear-search fix works. Write the PROMPTS.md log, and after it's saved,
   commit and push with the message "Phase 5: Collection search, filters,
   sort, pagination, and HTMX updates".

### Summary
- **Outcome:** Built Phase 5 of the plan:
  - `books/collection_query.py`, shared logic the Phase 6 API can reuse:
    - `CollectionParams.from_query()` cleans `q`, `status`, `min_rating`, and
      `ordering`, and unknown values fall back to the defaults
    - `filter_books()` applies search (title or authors, case-insensitive),
      minimum rating, and status
    - `status_counts()` counts all books and each status in one aggregate
      query, with every filter applied except status
    - an `ORDERINGS` table for the six sorts: empty ratings, years, and
      authors sort last, and ties break by title, ignoring case
  - the My Collection view pages at 20 with Django's `get_page`, sends
    `Vary: HX-Request`, and returns only the `_collection.html` fragment for
    HTMX swaps. HTMX history restores still get the full page.
  - the Variant D layout as one GET form (`_collection.html`), with:
    - a sidebar with the search box, status radios with counts and colored
      dots, minimum rating radios, and Reset filters
    - the sort dropdown at the top right and a result count
    - a "No books match these filters" empty state with Clear filters,
      separate from the "Your collection is empty" state
    - a `<noscript>` Apply button so the form works without JavaScript
  - `_pagination.html` with "Showing X–Y of N", Prev, Next, and numbered
    pages with ellipses. A `page_url` template tag copies the current query
    string and changes only `page`. The form has no page field, so any filter
    change starts at page 1.
  - HTMX attributes on the form: status, rating, and sort changes, Enter in
    the search box, pagination links, and the reset and clear links swap the
    whole collection area and push the URL
  - clearing an applied search (the X button or deleting the text) updates
    the collection right away, and the search box keeps focus after the swap
  - the Tailwind CSS rebuilt

  TDD covered three behaviors, each RED on an assertion and then GREEN:
  - status counts apply the search and rating filters but not the status
    filter (RED `{} == {'all': 3, …}`)
  - rating and year sorts put empty values last and break ties by title
    (RED: books came back newest first)
  - pagination links keep `q`, `status`, `min_rating`, and `ordering` and
    change only `page` (RED: no `rel="prev"` link)

  Normal tests cover:
  - each filter on its own, the other four orderings, and one combined test
  - 20 per page, and a filter change returning to page 1 (as the user asked)
  - out-of-range and invalid pages, and fallbacks for unknown values
  - the empty state, reset filters, and a single page having no page links
  - the full page vs. the HTMX fragment vs. a history restore, the
    `Vary` header, and the form's no-JS and HTMX attributes, including the
    clear-search trigger

  The suite went from 174 to 210 passing tests, with the script tests
  unchanged. Ruff check, Ruff format, and `manage.py check` are clean. The
  user verified everything in the browser, including offline mode.
- **Deviations:**
  - The user approved all three TDD candidates and asked for a normal test
    that changing a filter or search returns to page 1. Added: the form has
    no `page` field, and a filter request lands on page 1 with no Prev link.
  - After the browser check, the user asked for clearing the search box to
    update the collection right away, while typing still waits for Enter.
    Done with an extra `input` trigger that fires only when the box is empty
    and the input's `defaultValue` (the applied search) was not, plus an `id`
    on the input so HTMX keeps focus. The test checks only the attributes, so
    the user confirmed the behavior in the browser.
  - My own judgment calls, mentioned in my reports:
    - status and rating filters are radio buttons styled as DaisyUI menu
      items, so the form works without JavaScript
    - typing in the search box doesn't trigger a request on blur; only Enter
      does
    - `Vary: HX-Request` so a browser cache never serves the fragment as the
      full page
    - HTMX history restores get the full page
    - two empty states: one for an empty collection, one for no matches
    - the title sort uses the primary key as a tiebreak, and the author sort
      puts unknown authors last, as in the prototype
- **Sideways:**
  - Two Phase 2 collection tests failed once the new layout was in, because
    the design changed, not because of a bug:
    - the sidebar's rating filter now shows stars on every page, so the star
      test now looks only at the results section
    - the grid now pages at 20, so the 25-book seed test counts cards across
      both pages
    Both were mechanical repairs.
  - My first invalid-page test expected `page=-1` to show page 1, but
    Django's `get_page` treats any whole number outside the range (`0`,
    `-1`, `99`) as out of range and shows the last page. Following the PRD's
    "Django's safe page lookup", I moved `0` and `-1` to the out-of-range
    test and reported it.
  - A bash heredoc for appending the normal tests failed on quoting, so I
    appended them with the Edit tool instead.
  - `ruff format` rewrote `except (TypeError, ValueError)` into Python 3.14's
    unparenthesized form, which is valid for this project.
  - I read HTMX 2.0.4's trigger filter code to confirm that `target` in
    `change[target.type !== 'search']` resolves against the event before
    relying on it.

## 2026-11-15 — Phase 4: Open Library search and save from search

### Prompts
1. `/implement @prd/mychaptercollection.md @plans/mychaptercollection.md
   implement Phase 4. Show me the TDD candidates to approve first, then go
   through RED and GREEN without stopping unless something unexpected happens.`
2. Approved all three
3. Usability fix for the search page: for books already in my collection,
   make the cover and title clickable to open my saved book's detail page, the
   same way cards work on My Collection, not just the green badge. For books I
   haven't saved, make the title link to that book's page on Open Library in a
   new tab, so I can read more before saving.
4. Yes, update the cover and title right away after saving, so a newly saved
   card works the same as an owned one, while still keeping the page from
   reloading and keeping my other search results.
5. Found a bug during manual testing: after I save a book on the search page
   and then press the browser Back button, coming back to the search page
   shows the old version from before I saved, with a Save button on the book I
   just saved. The save itself worked, and the book shows correctly if I
   search again or open My Collection, so it looks like the browser is showing
   a cached copy. Please fix it so going back to a search page always shows
   the current saved state, for example by telling the browser not to cache
   the search page. Add a test that the search response has the no-cache
   header.

   Also, for books I haven't saved, make the cover open the book's Open
   Library page in a new tab too, not just the title, so it works the same way
   as cards for books I own.
6. Verified in the browser. Search, saving several books from one search, the
   instant card switch after saving, the Back button now showing saved books
   correctly, cover links for saved and unsaved books, duplicates showing the
   badge, the no-match message, the offline error with the collection link,
   and privacy with another user all work. Write the PROMPTS.md log, and after
   it's saved, commit and push with the message "Phase 4: Open Library search
   and save from search".

### Summary
- **Outcome:** Built Phase 4 of the plan:
  - `books/openlibrary.py`, the app's Open Library client, modeled on the
    script but separate from it (the script and its tests are unchanged). It
    makes one request per search for 20 results with only the needed fields,
    a 5-second timeout, and a `MyChapterCollection/1.0` User-Agent that adds
    `CONTACT_EMAIL` when set. It returns cleaned `SearchResult`s (authors
    joined, work key in short form, missing fields blank or None, docs without
    a key or title skipped). Each failure type raises `OpenLibraryError` with a
    friendly message: timeout, connection error, 403/429, 5xx, other HTTP
    errors, unreadable or wrongly shaped JSON, and other request errors.
  - a login-required, never-cached search page at `/books/search/` with:
    - result cards (cover or placeholder, title, author, year)
    - a comma-formatted total ("Found 1,234 matches") and a refine tip
    - a no-match message
    - on an error, a warning alert that keeps the query and links to My
      Collection
    - one owner-scoped lookup that marks owned results with an "In your
      collection" badge
  - cover and title links on every card: owned books open the saved book's
    detail page, and unsaved books open the Open Library work page in a new
    tab
  - `/books/save/` (POST only), which validates the posted facts with a new
    `SavedBookCreateForm`, sets the owner on the server, and starts the book
    as Want to read with total pages prefilled. It never calls Open Library.
    - With HTMX it returns the badge plus an out-of-band cover-and-title
      block (`_search_card_head.html`), so only that card switches to links to
      the saved book.
    - A duplicate returns the same badge and creates no row.
    - Invalid data re-renders that card's Save button with an inline error.
    - Without JavaScript it redirects back to the same search with a flash
      message.
  - the unused `books/placeholder.html` removed, `django.contrib.humanize`
    added, and the Tailwind CSS rebuilt

  TDD covered three behaviors, each RED on an assertion and then GREEN:
  - an Open Library failure shows the alert, keeps the query, and links to
    the collection (RED `500 == 200`)
  - owned results show the badge linking to the user's own saved book, and
    another user's copy doesn't count (RED: the Hobbit card still had Save)
  - an HTMX save creates one Want to read row with total pages and returns
    the badge, and a repeat save adds no row (RED `0 == 1`)

  Normal tests cover:
  - the client's request parameters, User-Agent, result cleanup, no-match
    results, and every error message
  - the search page: login required, no Open Library call for an empty query,
    rendering, total and tip, no matches, escaped titles, the save form's
    hidden fields, every error type, the card links, and the no-cache headers
  - save: login required, GET rejected, all facts copied, missing optional
    facts, `/works/` prefix stripping and duplicates, another user's copy not
    blocking a save, five kinds of invalid input, the no-JavaScript redirect
    and messages, ignoring an off-site return URL, the out-of-band card
    update, and a fixture that fails any save test that calls Open Library

  The suite went from 114 to 174 passing tests, with the script tests
  unchanged. Ruff check, Ruff format, and `manage.py check` are clean. The
  user verified everything in the browser, including offline mode and
  privacy with another user.
- **Deviations:**
  - The user approved all three TDD candidates as proposed.
  - After the first browser check, the user asked for clickable covers and
    titles: owned books open the saved book, and unsaved titles open Open
    Library in a new tab.
  - I pointed out that after a save only the button changed, so the card's
    title still pointed to Open Library. The user asked for the cover and
    title to switch right away, which I did with an HTMX out-of-band swap.
  - The user found the Back button bug and asked for a no-cache fix with a
    header test. They also asked for unsaved covers to open Open Library.
  - My own judgment calls, mentioned in my reports:
    - a `pageshow` handler that reloads the search page if the browser
      restores it from the back-forward cache despite `no-store`
    - an `IntegrityError` fallback for a double-click save
    - ignoring off-site `next` URLs on the no-JavaScript redirect
    - flash messages for no-JavaScript saves, duplicates, and failures
    - skipping search results with no key or title, since they can't be saved
    - a shared `fake_open_library` fixture in `tests/conftest.py` for the app
      tests (the script tests keep their own helpers)
    - `humanize` for the comma-formatted total, and removing the now-unused
      placeholder template
- **Sideways:**
  - The first error-handling RED was an exception, because Django's test
    client re-raises view errors. Setting `client.raise_request_exception =
    False` in that test turned it into the 500 a user would see, which failed
    on the status assertion.
  - The first save RED was a `DoesNotExist` crash from `.get()`. Adding a
    count assertion before it gave an assertion failure with the same
    meaning, noted as a mechanical repair.
  - One client test failed because the expected message contained
    parentheses, which `pytest.raises(match=...)` reads as a regex. I escaped
    them.
  - Two no-JavaScript save tests followed the redirect to the search page,
    which searched Open Library again and tripped the no-Open-Library
    fixture. They now check the redirect and read the flash message without
    following it.
  - My first version of the search page didn't stop browsers from caching
    it, so Back after a save showed the page from before the save. The user
    caught it in the browser, and `never_cache` plus the `pageshow` reload
    fixed it.

## 2026-11-15 — Phase 3: Book detail, edit, and remove

### Prompts
1. `/implement @prd/mychaptercollection.md @plans/mychaptercollection.md
   implement Phase 3. Show me the TDD candidates to approve first, then go
   through RED and GREEN without stopping unless something unexpected happens.`
2. Approved, all three. Make sure the normal tests also cover an invalid edit
   (current page above total pages, rating out of range) showing field errors
   without saving, and notes with HTML showing as escaped text.
3. Verified in the browser. Card links, valid and invalid edits, Finished
   auto-fill, escaped notes, the remove dialog with cancel and confirm,
   privacy with another user (404), and GET on delete (405, book not deleted)
   all work. Write the PROMPTS.md log, and after it's saved, commit and push
   with the message "Phase 3: Book detail, edit, and remove".

### Summary
- **Outcome:** Built Phase 3 of the plan:
  - `/books/<pk>/` (`books:detail`), login-required and owner-only through a
    `get_own_book` helper that looks up from `request.user.saved_books`, so
    another user's book is a 404. It shows:
    - a larger cover or the plain-book placeholder
    - title, authors, and first publish year
    - the status badge, stars, and "Page X of Y · N%" progress
    - notes as escaped plain text
  - `SavedBookEditForm` (`books/forms.py`) with only status, current page,
    total pages, rating (an "Unrated" choice plus 1–5), and notes. The
    model's `clean()` runs through it, so the page rule and Finished auto-fill
    apply. Saving uses Post/Redirect/Get with a "Saved" flash. Invalid input
    re-renders with field errors.
  - a Remove button that opens a DaisyUI `<dialog>` warning that status,
    rating, and notes are deleted too. Its confirm button posts to
    `/books/<pk>/delete/` (`books:delete`), which is `@require_POST`. After
    deleting, it redirects to My Collection with "Removed '<title>' from your
    collection."
  - collection cards wrapped in a link to the book's detail page, plus a
    `SavedBook.get_absolute_url()`
  - the Tailwind CSS rebuilt for the new template classes

  TDD covered three behaviors, each RED on an assertion and then GREEN:
  another user gets 404 on view, edit, and delete (RED `200 == 404` against
  stub views); an edit saves the tracking fields and ignores posted book facts
  (RED `'want_to_read' != 'reading'`); delete refuses GET with 405 and a POST
  deletes, redirects, and shows the message (RED `200 == 405`). Normal tests
  cover login required, the page content and locked fields not appearing in
  the form, the cover placeholder, card links, the "Saved" redirect, invalid
  edits, Finished auto-fill through the form, escaped notes, and the remove
  dialog. The invalid edits checked are current page above total, rating 6,
  rating 0, total pages 0, current page −1, and an unknown status; each shows
  its field error and leaves the row unchanged. The suite went from 97 to 114
  passing tests, with the script tests unchanged. Ruff check and format are
  clean. The user verified everything in the browser.
- **Deviations:**
  - The user approved all three TDD candidates and asked for normal tests of
    invalid edits (current page above total, rating out of range) and escaped
    HTML notes. Both were added; the invalid-edit test also covers total
    pages 0, a negative current page, and an unknown status.
  - My own judgment calls, mentioned in the report:
    - after a rejected edit, the view reloads the book from the database so
      the header shows the stored values while the form keeps what was typed
      (validation had copied the rejected values onto the instance)
    - the detail page shows progress whenever total pages is known, including
      0%, unlike the cards, which hide it for Want to read and page 0
    - the form's fields are rendered by hand in the template rather than
      through the accounts `_form_fields.html` include, which only handles
      inputs, not selects or a textarea
- **Sideways:**
  - Ruff flagged RUF012 on an unused `widgets` dict in the form's `Meta`. It
    was removed instead of suppressed, since the template renders the textarea
    itself.
  - `ruff format` reformatted the new test file once.
  - To confirm the status and rating selects pre-select the right option on
    GET and after an invalid POST, I ran a throwaway pytest file from the
    scratchpad, outside the repo. Both cases were correct.
  - The first try at adding this entry failed because the text I anchored on
    didn't match the file's indentation, so I anchored on the Phase 2 heading
    instead.

## 2026-11-14 — Phase 2: SavedBook model, demo seed, and collection grid

### Prompts
1. `/implement @prd/mychaptercollection.md @plans/mychaptercollection.md
   implement Phase 2. Show me the TDD candidates to approve first, then go
   through RED and GREEN without stopping unless something unexpected happens.`
2. Approved, all three. Also add a fourth TDD behavior: My Collection only
   shows the logged-in user's books, never another user's. That's the core of
   requirement 6. Make sure the other model rules (title required, rating 1-5,
   current page not above total pages, unique owner plus work key, default
   status) and the grid display rules get normal tests.
3. Verified in the browser. Covers and placeholders, badge colors, stars,
   progress bars, the welcome back message, privacy with a new user, and
   offline mode all work. I'm okay with Finished auto-correcting the current
   page instead of rejecting it. One fix: long titles like The Hitchhiker's
   Guide to the Galaxy wrap to two lines and push the author and badge lower
   than the other cards in the row. Limit titles to two lines with an
   ellipsis, and give every card's title the same two-line height so all the
   cards in a row line up. Show the full title on hover.
4. The title fix works, the cards line up now. Write the PROMPTS.md log, and
   after it's saved, commit and push with the message "Phase 2: SavedBook
   model, demo seed, and collection grid".

### Summary
- **Outcome:** Built Phase 2 of the plan:
  - the `SavedBook` model and migration with every PRD field. It has:
    - a `WorkKeyField` that stores the short `OL…W` form, plus shared
      `normalize_work_key` and `validate_work_key` helpers for the Phase 6 API
    - a non-blank title validator
    - rating 1–5 or empty, and total pages 1 or more
    - the current-page-not-above-total rule
    - Finished auto-fill in both `save()` and `clean()`
    - an owner plus work key unique constraint with the message "This book
      is already in your collection."
    - display helpers (author fallback, cover URL, progress percent, when to
      show progress)
  - a `seed_demo` command that creates or reuses `demo`, prints its
    local-only password, and adds 25 hard-coded books. The work keys, cover
    IDs, and page counts were looked up once from Open Library, and every
    cover was checked with `?default=false`. The books cover all four
    statuses, with 4 lacking a cover and 3 lacking total pages. Reruns skip
    books the user already has.
  - a login-required My Collection page built from the current user's books.
    It shows a 5-per-row cover grid with:
    - the image, or the plain-book placeholder (with an `onerror` swap)
    - an "Unknown author" fallback
    - colored soft status badges
    - stars only when rated
    - a progress bar only when total pages is known, progress is above 0,
      and the status is not Want to read
    - an empty state
  - the model registered in the admin, a README "Demo data" section with the
    local-only password warning, and `seed_demo` added to CLAUDE.md

  TDD covered four behaviors, each RED then GREEN: work key normalization
  and validation, Finished auto-fill, the seed being safe to run twice, and
  the collection showing only the owner's books. Normal tests cover the other
  model rules, the rest of the seed command, and every grid display rule. The
  suite went from 44 to 97 passing tests, with the script tests unchanged.
  Ruff and `manage.py check` are clean. The user verified everything in the
  browser, including offline mode and privacy with a new user.
- **Deviations:**
  - The user added a fourth TDD behavior (collection privacy) beyond the
    skill's limit of three, and asked for normal tests of the other model
    rules and the grid display rules.
  - After the browser check, the user asked for card titles clamped to two
    lines with an ellipsis, a fixed two-line height so cards line up, and the
    full title on hover. Done with `line-clamp-2 h-[2lh]` and a `title`
    attribute, plus a test for the hover title.
  - The user accepted my judgment call that Finished corrects an
    overshooting current page instead of rejecting it.
  - Other judgment calls I made, all mentioned in my reports:
    - kept the Open Library values exactly as returned, including Little
      Women's 1848 year and translators in some author lists
    - switched Django list class attributes to tuples
    - exempted only generated migrations from Ruff's RUF012
- **Sideways:**
  - The seed test's RED was a `ValidationError` crash from the model's
    duplicate check, not an assertion failure. I kept it and flagged it,
    because the crash was the missing behavior itself, not missing scaffolding.
  - I first mistyped two author names in the seed data ("Daḳner", and a
    precomposed "Brontë"). I caught them against the lookup output before any
    test ran and fixed them to Open Library's exact strings.
  - Ruff 0.17's defaults now include RUF012, which Phase 1 never triggered.
    Switching `Meta` to tuples changed the migration state, so the
    uncommitted `0001_initial` was regenerated twice.
  - My first grep for escaped Tailwind classes (`xl:grid-cols-5`,
    `aspect-[2/3]`) found nothing because of CSS escaping. A Grep with the
    escaped pattern confirmed they were built.

## 2026-11-14 — Phase 1: project skeleton, accounts, and app shell

### Prompts
1. `/implement @prd/mychaptercollection.md @plans/mychaptercollection.md
   implement Phase 1. Show me the TDD candidates to approve first, then go
   through RED and GREEN without stopping unless something unexpected happens.`
2. Approved, all three. Also add normal tests that the home page loads for
   logged-out visitors, that login and logout work, and that flash messages
   show in the base layout.
3. Verified in the browser. Sign-up with the welcome message, logout, the
   return-to after login, and the wrong password error all work. One change: I
   want a "Welcome back, <username>!" flash message every time someone logs
   in, so login gives the same kind of confirmation as sign-up and logout. Add
   a test for it too.
4. The welcome back message works. Now add the real commands to CLAUDE.md
   since they exist: migrate, runserver, the tailwind build command, pytest,
   and ruff. Then write the PROMPTS.md log. After the log is saved, commit and
   push with the message "Phase 1: Project skeleton, accounts, and app shell".

### Summary
- **Outcome:** Built Phase 1 of the plan:
  - Django 6.1 project (`config` settings, `books` and `accounts` apps) under
    uv with SQLite
  - Tailwind + DaisyUI through `django-tailwind-cli`. The DaisyUI setting was
    confirmed in the package source as `TAILWIND_CLI_USE_DAISY_UI = True`,
    which downloads the standalone `tailwindcss-extra` binary (pinned to
    2.10.35). No Node.
  - a custom `chapter` DaisyUI theme with the prototype's warm base colors
  - HTMX 2.0.4 as a local static file
  - base layout with the navbar, a user menu with POST logout, and flash
    messages
  - public home page
  - sign-up with auto-login, login, and logout
  - login-required placeholder pages for My Collection and Find books
  - an autouse fixture that blocks all sockets in tests

  TDD covered three behaviors, each RED on an assertion then GREEN: sign-up
  creates and logs in the user; a protected page redirects to login with
  `?next=` and returns there after login; an unfaked network call fails
  loudly with an error that isn't a `requests` error. Normal tests cover the
  home page, login (valid and wrong password), logout (and that it is
  POST-only), the navbar, mismatched sign-up passwords, and flash messages
  after sign-up, login, and logout. The suite went from 28 to 44 passing
  tests, with the script tests unchanged. CLAUDE.md gained a Commands section
  and the README gained run instructions.
- **Deviations:**
  - The user added extra normal tests to the approved TDD set.
  - After the browser check, the user asked for a "Welcome back, <username>!"
    message on every login. Done with a small `LoginView` subclass, with
    tests that it shows after login, not after a failed login, and not on top
    of the sign-up welcome.
  - My own judgment calls, mentioned in the reports:
    - added "Welcome, <username>! Your collection is ready." on sign-up and
      "You've been logged out." on logout, so the flash test had real
      messages to check
    - used per-view `@login_required` instead of Django's
      `LoginRequiredMiddleware`, because the middleware would also redirect
      the Phase 6 API, which must return 401
    - committed the built `static/css/tailwind.css` so the app is styled
      right after cloning, and git-ignored the 111 MB binary
- **Sideways:**
  - The first sign-up RED crashed with `DoesNotExist` from `.get()` rather
    than failing an assertion. I switched it to a `filter().first()`
    existence assertion with the same meaning, noted as a mechanical repair.
  - Ruff flagged the guard's exception name (N818), so it became
    `NetworkAccessBlockedError`. Ruff also cleaned unused imports and quote
    style in Django's generated files.
  - A first Grep for the DaisyUI setting in the package returned nothing.
    Listing the files and reading `config.py` found it.
  - One PowerShell command failed on a quoting error and was redone with
    Grep.
  - The "Welcome back" tests were written alongside the code, not
    test-first, since it was a requested change outside the approved TDD set.

## 2026-11-14 — Created the initial CLAUDE.md

### Prompts
1. (Pasted) Create the initial CLAUDE.md for this project.

   Keep it to about 20-30 lines. Include only:
   1. A one-line project description.
   2. The approved technology stack and package manager.
   3. Durable, project-wide architecture decisions already established in the
      PRD.
   4. Short pointers to the PRD, plan, and prototypes instead of repeating
      their details.

   Do not add commands yet because the project tooling has not been installed
   or verified.
   Do not predict project structure, paths, template conventions, URL
   conventions, or testing commands that do not exist yet.
   Do not copy business requirements, user stories, implementation phases,
   rejected alternatives, or detailed feature rules into CLAUDE.md.
   Do not invent new architectural conventions.
2. Append a session log to PROMPTS.md at the repo root, under today's date,
   newest entry at the top. Record every prompt I gave you this session, in
   order, including any corrections. End the entry with a short summary: the
   outcome, any places where I deviated from a recommended answer or asked
   follow-up questions, and anything that went sideways.

### Summary
- **Outcome:** After reading the PRD, the plan, the README, and the list of
  tracked files, I wrote a 29-line `CLAUDE.md` at the repo root. It has:
  - a one-line description of the app
  - the stack: uv, Django with SQLite, DRF with session and token auth,
    Tailwind and DaisyUI via `django-tailwind-cli` with no Node, HTMX as a
    pinned local file, and pytest with pytest-django
  - seven architecture decisions taken from the PRD: book details copied
    into one local row per user per book, Open Library called only from the
    search page, owner-scoped queries that return 404 for other users' books,
    validation in the model, book details locked after saving, offline tests,
    and the existing script and its tests left unchanged
  - pointers to the PRD, the plan, the prototype (Variant D), and the API
    research doc

  It has no commands, URLs, test commands, user stories, or phases. Nothing
  was committed.
- **Deviations:** No recommendations were offered and there were no follow-up
  questions. One judgment call I made myself: I left out the PRD's planned
  `config` settings package and `books`/`accounts` app names, because those
  folders don't exist yet and the prompt said not to predict project
  structure. They can be added once the skeleton is built.
- **Sideways:** Nothing major. An early file search also matched files inside
  `.venv`, which added noise but didn't change anything. The first try at
  adding this entry failed because the text I tried to match didn't match the
  file exactly, so I anchored the edit on the previous entry's heading
  instead.

## 2026-11-14 — Broke the MyChapterCollection PRD into a 6-phase plan

### Prompts
1. `/prd-to-plan @prd/mychaptercollection.md`
2. Let's merge it down to 6 phases. Merge 3 and 4 since search and save are on
   the same page and I'd test them together. Merge 5 and 6 since remove is
   small and on the same detail page. Merge 7 and 8 since the HTMX updates are
   on the same collection page and I'd test them with the same clicks. Merge 9
   and 10 into one API phase since it's the same viewset. Keep 1 and 2 as they
   are. Keeping the demo seed in Phase 2 is good. The /books/ and /api/ URLs
   are fine. Go ahead and write the final plan file.
3. One change: swap Phases 3 and 4. In the current order, the Phase 3 "In your
   collection" badge links to the book detail page, but that page isn't built
   until Phase 4, so the link would 404 when I test Phase 3 in the browser.
   Detail, edit, and remove don't depend on search since the demo seed already
   gives me books to open, so build detail/edit/remove as Phase 3 and
   search/save as Phase 4. Update the plan file.
4. Append a session log to PROMPTS.md at the repo root, under today's date,
   newest entry at the top. Record every prompt I gave you this session, in
   order, including any corrections. End the entry with a short summary: the
   outcome, any places where I deviated from a recommended answer or asked
   follow-up questions, and anything that went sideways.

### Summary
- **Outcome:** After a look at the repo (still only the script, its tests,
  the research doc, the prototype, and the PRD), the plan was written to
  `plans/mychaptercollection.md`. Its header records the durable decisions:
  - the `config`/`books`/`accounts` layout
  - the `/`, `/accounts/…`, `/books/…`, and `/api/…` URLs, with `pk`s and the
    `books:` and `accounts:` namespaces
  - the `SavedBook` model and its rules, and the locked vs. editable fields
  - owner-scoped 404s and session plus token API auth
  - the `q`/`status`/`min_rating`/`ordering`/`page` params shared by the
    website and the API
  - the Open Library limits and the offline testing rules

  The final phases are:
  1. skeleton, accounts, and shell
  2. model, demo seed, and basic grid
  3. detail, edit, and remove
  4. search and save
  5. collection filters, sort, pagination, and HTMX
  6. REST API

  Every phase ends with the full suite passing, including the 28 script tests,
  unchanged. No code was written, no tests were run, and nothing was
  committed.
- **Deviations:**
  - I proposed 10 phases. The user merged them down to 6: search with save,
    detail with remove, filters with HTMX, and both API phases into one.
  - The user accepted the recommended URLs and kept the demo seed in Phase 2.
  - The user then reordered detail/edit/remove ahead of search/save.
- **Sideways:**
  - My proposed order (kept through the first written plan) put the search
    page's "In your collection" badge, which links to `/books/<pk>/`, in the
    phase before the detail page existed. The badge link would have 404'd in
    browser testing.
  - The user caught this and had the phases swapped. The plan now says the
    collection cards link to detail in Phase 3, and Phase 4 checks that both
    owned-result badges and newly saved badges link to the detail page.

## 2026-11-14 — Designed MyChapterCollection, prototyped the collection page, and wrote the PRD

### Prompts
1. `/grill-me` I'm building a new Django app called MyChapterCollection. It's a
   personal reading tracker where users search for books through Open Library,
   save the ones they want to their own collection, and keep track of their
   reading status, progress, ratings, and notes.

   I already picked Open Library based on my research in
   docs/research/external-api-options.md, and scripts/search_books.py already
   proves the API works. Use both of those as a starting point.

   Tech stack:
   - Django and Django REST Framework
   - SQLite
   - uv for packages (the project is already set up at the repo root)
   - Ruff for linting and formatting
   - Tailwind with DaisyUI for styling
   - HTMX for interactivity
   - pytest with pytest-django for testing

   Business requirements:
   1. The app has one clear purpose that solves a real user need.
   2. Users find books through the Open Library API.
   3. Users can save books locally so they still show up if Open Library goes
      down.
   4. Users can add their own info to saved books, like reading status, current
      page, rating, and notes.
   5. Users can search, filter, sort, and paginate their saved books, all from
      local data.
   6. Users have to log in to manage their books. Access rules have to be
      enforced on both the website and the API.
   7. The app has its own API to list, create, update, and delete saved books.
   8. The app shows a helpful message if Open Library is down or a request
      fails.

   I want to keep the scope focused so it's something I can build and test
   well.
2. Let's do A, one SavedBook table.
3. Let's do option a, the client sends the book fields. But lets still validate
   them on the server. The work key should match OpenLibrary's format, and
   title should also be required.
4. Option A and show a messgae "In your collection" badge when in search
   reuslts.
5. B, the four fields plus total_pages. Also, for later in the design, I want
   the app to look clean and modern, and I want book covers shown on both the
   search results and my collection page. If a book has no cover or the image
   doesn't load, show a placeholder instead of a broken image.
6. B, four statuses with Want to read as the default.
7. B, auto-fill the page when marked Finished
8. Lets do option a
9. Let's do option b. And before we move on, I would want to do a prototype of
   the collection page layout. (Pasted with it:) `/prototype` Build 3
   structurally different versions of the My Collection page using Tailwind and
   DaisyUI from the CDN, so I can compare them side by side. Use around 15
   realistic fake books spread across all 4 statuses, with some rated and some
   unrated, some with total pages and some without, and a few with no cover so
   I can see the placeholder.

   Each version needs the controls we just decided: one search box for title or
   author, a status filter, a minimum rating filter, the 6 sort options, and
   pagination. Each book should show its cover, title, author, status badge,
   rating, and a progress bar when total pages is known.

   1. A cover grid of cards with the search and filters in a bar across the
      top.
   2. A list or table layout with the filters in a sidebar.
   3. A layout of your choice that's different from the first two.

   I want it to look clean and modern, not crowded. Make the search, filters,
   sort, and pagination actually work in memory so I can feel how each layout
   works.
10. I'm going with a mix of A and B. I want B's left sidebar for the search box,
    the status filter with the count next to each status, the minimum rating
    filter, and the reset filters link, with the sort dropdown at the top right
    like in B. For the books themselves I want A's cover grid, but with smaller
    covers so more books fit on the screen, around 4 per row next to the
    sidebar.

    Other changes:
    - The no cover placeholder should be smaller and look nicer, not a big
      empty gray box.
    - Status badges should be colored like in B, not plain text.
    - Keep the title, author, status, rating, and progress bar under each
      cover.
    - Clicking a book opens its own detail page where I can edit it, instead of
      a side panel.

    I picked this because A's covers looked the most like a real reading app
    but were too big, and B's sidebar kept the filters organized without
    crowding the page. I didn't go with C because the detail panel adds more
    HTMX work.
11. (Pasted) This is close. A few changes for the final design:
    - Make the covers a little smaller and fit 5 per row, since there's empty
      space on the sides.
    - Hide the progress bar for Want to read books, or when progress is 0.
    - Don't show "Not rated" on cards, just leave the rating empty if there
      isn't one.
    - Use a warm off-white background instead of plain white.
    Otherwise this is the layout I want. Let's continue with the interview.
12. Lets do option a. Lets also add a remove button on the detail page with a
    confirm prompt before it deletes the book.
13. Option B, the DaisyUI modal
14. Option a
15. Option A, return 404
16. Option B, session plus token
17. Option B, lock the book facts
18. Option a. Also make sure that saving a book from the results only swaps
    that book's save button for the "in your collection" badge, and doesn't
    reload the page or clear my search results, so I can keep saving more books
    from the same result.
19. Option a. When you move the search logic into the app, make sure
    scripts/search_books.py still works on its own and its tests keep passing,
    since the script is also graded.
20. Option A, leave the script untouched
21. Option A, config plus books and accounts
22. Option b
23. Option C, make sure that moving to the next page keeps my search, filters,
    and sortsm and that changing a filter or search sends me back to page 1
24. Option A, use monkeypatch like the script's tests
25. C, a seed_demo command. Use real Open Library work keys and cover IDs for
    the sample books so real covers show up, and keep a few with no cover to
    show the placeholder.
26. `/to-prd`
27. Append a session log to PROMPTS.md at the repo root, under today's date,
    newest entry at the top. Record every prompt I gave you this session, in
    order, including any corrections. End the entry with a short summary: the
    outcome, any places where I deviated from a recommended answer or asked
    follow-up questions, and anything that went sideways.

### Summary
- **Outcome:** A 22-question grill-me session settled the full app design:
  - one `SavedBook` table with book facts copied from Open Library, locked
    after create except total pages
  - 4 statuses, rating 1–5, a page rule, and Finished auto-filling the
    current page
  - top-20 search with an HTMX per-card Save swap and no Open Library call on
    save; one-attempt, 5-second search error handling
  - an HTMX-swapped collection page with URL-based filters, sort, and
    pagination
  - a form-based detail page with a DaisyUI remove modal
  - Django built-in auth plus sign-up, with 404 for other users' books
  - a DRF API with session and token auth
  - a `config`/`books`/`accounts` layout, `django-tailwind-cli` with DaisyUI
    (no Node), monkeypatch-based offline tests, and a `seed_demo` command
  
  A prototype, `prototypes/collection-layouts.html`, built three layouts (A
  cover grid, B table with sidebar, C list/detail) and then a chosen Variant D.
  D combines B's sidebar with A's grid at 5 per row, a nicer cover
  placeholder, colored badges, and a warm off-white theme. The decision is
  recorded at the top of the file. The PRD was written to
  `prd/mychaptercollection.md` with 75 user stories. The existing script and
  its tests were not modified. All 28 tests passed when checked during the
  session. Nothing was committed.
- **Deviations:** Every question was answered with the recommended option.
  Additions and changes beyond the recommendations:
  - server-side validation of the work key format and required title
  - covers on search and collection pages, with a placeholder for missing or
    broken images
  - a prototype detour before continuing the interview
  - a mixed A+B layout instead of any single variant, then a second round of
    tweaks (5 per row, progress-bar hiding, no "Not rated", warm background)
  - a Remove button with confirmation, which led to the modal question
  - Save on search swapping only that card's button
  - the graded script staying standalone with its tests passing, which led to
    the leave-it-untouched question
  - pagination keeping filters and filter changes resetting to page 1
  - seed data using real Open Library keys and cover IDs
- **Sideways:**
  - The first combined file read exceeded the output limit and had to be read
    from the saved tool-output file.
  - `python` isn't on PATH in this Windows shell (the Microsoft Store alias
    fired), so the npm version lookup was rerun with `uv run python`.
  - Node isn't installed, so the prototype's JavaScript couldn't be
    syntax-checked, and I never viewed the rendered page myself. It was only
    opened in the user's browser for them to review.
  - The prototype remembers the last-viewed variant, so after Variant D was
    added the user may have needed to press the arrows to reach it.
  - Two items are still unverified and are flagged in the PRD: the exact
    `django-tailwind-cli` setting that enables DaisyUI, and the real Open
    Library work keys and cover IDs for `seed_demo`. Those were deliberately
    not written from memory and must be looked up during the build.

## 2026-11-14 — Picked Open Library and built a tested console search script

### Prompts
1. `/research` I'm starting Project 2 and I need help picking an external API to
   build around. The app has to let users search for stuff through an outside
   API, save the items they pick to my own database, and then add their own
   info to them like notes, ratings, or a status. I haven't picked a topic yet,
   so look at a few options like books, recipes, video games, and movies/TV, and
   tell me which providers would actually work.

   My stack is Django, Django REST Framework, SQLite, uv, and Ruff. I get to
   pick the rest on my own and I'm leaning toward Tailwind with DaisyUI and
   HTMX.

   These are the project requirements I have to meet:
   1. The app has one clear purpose that solves a real user need.
   2. Users find items through an external API that's free enough to cover the
      whole project.
   3. Users can save items locally so they still show up if the API goes down.
   4. Users can add their own info to saved items (notes, ratings, status,
      progress, etc).
   5. Users can search, filter, sort, and paginate their saved items, all from
      local data.
   6. Users have to log in to manage their data, and the access rules work on
      both the website and the API.
   7. The app has its own API to list, create, update, and delete saved
      entries.
   8. The app shows a helpful message if the provider is down or a request
      fails.

   For each provider, check the official docs and terms and tell me:
   - if it has a search endpoint and a detail endpoint, and what fields come
     back
   - if I need an account or API key, and how easy it is to get one
   - what the free tier limits are (rate limits, request caps, anything locked
     behind paying)
   - if the terms let me save results in my own database
   - one sample request URL I can test myself

   Then compare them against my requirements, mostly 2, 3, 4, and 8 since those
   depend on the API. Give me your top pick and a runner-up and explain why.
   Cite the official source for every claim so I can check it myself. I'd
   rather use something that's quick to set up and doesn't need a long approval
   process for an API key.
2. `/grill-me` I will go with Open Library from the research in
   docs/research/external-api-options.md. Before I design the full app, I want
   a small console script that proves I can actually get data from it. The
   script should:
   - ask me to type in a search
   - make a real request to Open Library with what I typed
   - show the results in a clean, easy to read way
   - handle it when nothing matches my search
   - handle it when the request fails, like a timeout or no connection

   Set it up with uv since the Django project will use it later. Open Library
   doesn't need an API key, but it asks apps to send a User-Agent header with
   an app name and contact email. Keep my email in a .env file instead of
   hardcoding it in the script.
3. Let's do A. Also this script should not be throaway. It will be graded
   alopg with my whole project, so I would like it to be permanently in my
   repo. My second script that calls my own Django API should also go in
   scripts/ later on.
4. Let's go with A, requests. Also make sure every requests always passes a
   timeout.
5. Let's go with A, python-dotenv. In the case that CONTACT_EMAIL is missing,
   do not crash. Instead print a clear warning message that tells me how to set
   up the .env file and still run the search without the email since Open
   Library doesn't require an email for use.
6. Let's go with B, keep asking until I quit or type q.
7. Let's go with A, plain print as a numbered list. You can also keep the
   formatting in its own funcion like you suggested
8. Let's go with A, first 10 results only.
9. Let's go with B, separate messages for each case.
10. Let's go with B, pytest with fake responses.
11. Let's go with B, defaults plus extra rules.
12. Let's go with A, general search.
13. yes, go ahead and build it
14. Walk me through how this script makes the request, gets the response, and
    displays the results. Point me to the specific functions and lines.
15. Append a session log to PROMPTS.md at the repo root, under today's date,
    newest entry at the top. Record every prompt I gave you this session, in
    order, including any corrections. End the entry with a short summary: the
    outcome, any places where I deviated from a recommended answer or asked
    follow-up questions, and anything that went sideways.
16. I also ran the script myself before this log. I tested a real search (the
    hobbit), a search with no matches (asdkjhqwe), and a failed request by
    turning off my Wi-Fi, then turned it back on and searched again. All of
    them worked, and result 10 for the hobbit showed "Unknown author"
    correctly. Add this message to today's entry as the next prompt, and
    update the Outcome to include my manual testing.

### Summary
- **Outcome:** A background research agent compared ten providers (Open
  Library, Google Books, TheMealDB, Spoonacular, Edamam, RAWG, IGDB, TMDB,
  OMDb, TVmaze) against official docs and terms and wrote
  `docs/research/external-api-options.md`. It recommended Open Library, with
  TVmaze as runner-up. A ten-question grill-me session then settled the design
  for a console search script, which was built and kept: a root uv project on
  Python 3.14 (`pyproject.toml`, `uv.lock`), `scripts/search_books.py`,
  `tests/test_search_books.py` (28 offline pytest tests using monkeypatched
  fake responses), `.env.example`, and a README with setup, run, and test
  commands and a manual checklist. All tests, `ruff check`, and
  `ruff format --check` pass. A live run against Open Library confirmed a real
  search and the no-results case. A real unreachable host and a tiny timeout
  confirmed the connection and timeout messages. The 503/429/bad-response
  paths were verified only by the offline tests. The user also manually tested
  the script: a real search ("the hobbit"), a no-match search ("asdkjhqwe"),
  and a failed request with Wi-Fi turned off, followed by a successful search
  after turning it back on. All worked, and result 10 for "the hobbit" showed
  "Unknown author" correctly. Nothing was committed.
- **Deviations:** Every grill-me answer matched the recommended option. Added
  requirements beyond the recommendations: the script is permanent and graded,
  not throwaway, which corrected how question 1 had framed it; future scripts
  go in `scripts/`; every request must pass a timeout; and a missing
  `CONTACT_EMAIL` must warn with setup instructions and still search.
  Follow-up question: a line-by-line walkthrough of how the script makes the
  request, handles the response, and displays results.
- **Sideways:**
  - The research agent's WebFetch got a 403 on the IGDB docs, so it read the
    official page with curl instead. Its report listed several claims it could
    not verify, and those are marked in the research file.
  - The first `ruff check` flagged import order (I001) because Ruff treated
    `search_books` as third-party. Fixed by adding `src = [".", "scripts"]` to
    the Ruff config. `ruff format` also reformatted two lines.
  - The live run showed result 10's detail lines misaligned under a two-digit
    number. Fixed `format_book()` to compute the indent and added a test.
  - Using PowerShell `Set-Content` to update a test constant added a UTF-8
    BOM to the test file. `ruff format --check` caught it, and it was stripped
    with `sed`.
  - Piping test input through PowerShell put an invisible BOM character at the
    start of the first live query. This was an artifact of the test command,
    not the script, so the script was not changed.
  - VS Code reports "package not installed" for `requests` and `python-dotenv`
    because its selected interpreter isn't the project `.venv`. Not yet fixed;
    the user needs to select `.venv` as the interpreter.