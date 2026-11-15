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