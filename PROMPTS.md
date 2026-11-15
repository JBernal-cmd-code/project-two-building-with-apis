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
  paths were verified only by the offline tests. Nothing was committed.
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
    I also ran the script myself before this log. I tested a real search (the hobbit), a search with no matches (asdkjhqwe), and a failed request by turning off my Wi-Fi, then turned it back on and searched again. All of them worked, and result 10 for the hobbit showed "Unknown author" correctly. Add this message to today's entry as the next prompt, and update the Outcome to include my manual testing.