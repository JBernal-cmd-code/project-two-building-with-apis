"""My Collection: search, filters, sort, pagination, and HTMX updates."""

import re
from html import unescape
from urllib.parse import parse_qs

import pytest
from django.urls import reverse

from books.models import SavedBook

pytestmark = pytest.mark.django_db

PASSWORD = "a-Long-unusual-pass-42"


@pytest.fixture
def reader(django_user_model):
    return django_user_model.objects.create_user(username="reader", password=PASSWORD)


@pytest.fixture
def other(django_user_model):
    return django_user_model.objects.create_user(username="other", password=PASSWORD)


def save_book(owner, title, **fields):
    """Save a book with a work key derived from a per-test counter."""
    save_book.counter += 1
    return SavedBook.objects.create(
        owner=owner, ol_work_key=f"OL{save_book.counter}W", title=title, **fields
    )


save_book.counter = 0


def get_collection(client, user, **params):
    client.force_login(user)
    response = client.get(reverse("books:collection"), params)
    assert response.status_code == 200
    return response


def status_counts(html):
    return {
        key: int(count)
        for key, count in re.findall(r'data-status-count="(\w+)">(\d+)<', html)
    }


def card_titles(html):
    """Titles of the rendered book cards, in page order."""
    return re.findall(r'<h3[^>]*title="([^"]*)"', html)


@pytest.mark.parametrize(
    ("ordering", "field"),
    [("-rating", "rating"), ("-first_publish_year", "first_publish_year")],
)
def test_rating_and_year_sorts_put_empty_values_last_then_sort_by_title(
    client, reader, ordering, field
):
    # Created out of order so the default (newest first) can't pass by accident.
    save_book(reader, "Beta", **{field: 5})
    save_book(reader, "No Value", **{field: None})
    save_book(reader, "Gamma", **{field: 3})
    save_book(reader, "Alpha", **{field: 5})

    response = get_collection(client, reader, ordering=ordering)

    assert card_titles(response.content.decode()) == [
        "Alpha",
        "Beta",
        "Gamma",
        "No Value",
    ]


def link_query(html, rel):
    """The query parameters of the pagination link with the given ``rel``."""
    tag = re.search(rf'<a\b[^>]*\brel="{rel}"[^>]*>', html)
    assert tag, f'no rel="{rel}" link'
    href = unescape(re.search(r'href="([^"]*)"', tag.group()).group(1))
    path, _, query = href.partition("?")
    assert path in ("", reverse("books:collection"))
    return {key: values for key, values in parse_qs(query).items()}


def test_pagination_links_keep_filters_and_sort_and_change_only_the_page(
    client, reader
):
    for n in range(45):
        save_book(
            reader, f"Tolkien book {n}", authors="Tolkien", status="reading", rating=4
        )
    filters = {
        "q": "tolkien",
        "status": "reading",
        "min_rating": "4",
        "ordering": "title",
    }

    html = get_collection(client, reader, page="2", **filters).content.decode()

    expected = {key: [value] for key, value in filters.items()}
    assert link_query(html, "prev") == expected | {"page": ["1"]}
    assert link_query(html, "next") == expected | {"page": ["3"]}


def test_status_counts_respect_search_and_rating_but_not_status(client, reader, other):
    tolkien = {"authors": "J.R.R. Tolkien"}
    save_book(reader, "The Hobbit", status="reading", rating=5, **tolkien)
    save_book(
        reader, "The Fellowship of the Ring", status="finished", rating=4, **tolkien
    )
    save_book(reader, "The Two Towers", status="finished", rating=4, **tolkien)
    # Filtered out by the rating filter:
    save_book(
        reader, "The Return of the King", status="want_to_read", rating=3, **tolkien
    )
    save_book(reader, "The Silmarillion", status="finished", **tolkien)
    # Filtered out by the search:
    save_book(reader, "Dune", status="finished", rating=5, authors="Frank Herbert")
    # Another user's matching book never counts.
    save_book(other, "Unfinished Tales", status="finished", rating=5, **tolkien)

    response = get_collection(
        client, reader, q="tolkien", min_rating="4", status="reading"
    )

    assert status_counts(response.content.decode()) == {
        "all": 3,
        "want_to_read": 0,
        "reading": 1,
        "finished": 2,
        "abandoned": 0,
    }


# --- Filters on their own -------------------------------------------------


def test_search_matches_title_or_authors_case_insensitively(client, reader):
    save_book(reader, "The Hobbit", authors="J.R.R. Tolkien")
    save_book(reader, "A Tolkien Companion", authors="J.E.A. Tyler")
    save_book(reader, "Dune", authors="Frank Herbert")

    by_author = get_collection(client, reader, q="TOLKIEN").content.decode()
    by_title = get_collection(client, reader, q="hobb").content.decode()

    assert sorted(card_titles(by_author)) == ["A Tolkien Companion", "The Hobbit"]
    assert card_titles(by_title) == ["The Hobbit"]


def test_search_keeps_the_text_in_the_box(client, reader):
    html = get_collection(client, reader, q="  dune  ").content.decode()

    assert 'name="q" value="dune"' in html


def test_status_filter_shows_only_that_status(client, reader):
    save_book(reader, "Reading One", status="reading")
    save_book(reader, "Finished One", status="finished")

    html = get_collection(client, reader, status="finished").content.decode()

    assert card_titles(html) == ["Finished One"]
    assert 'name="status" value="finished" class="sr-only" checked' in html


@pytest.mark.parametrize(
    ("min_rating", "expected"),
    [("4", ["Five", "Four"]), ("5", ["Five"]), ("1", ["Five", "Four", "Two"])],
)
def test_min_rating_filter_hides_lower_and_unrated_books(
    client, reader, min_rating, expected
):
    save_book(reader, "Five", rating=5)
    save_book(reader, "Four", rating=4)
    save_book(reader, "Two", rating=2)
    save_book(reader, "Unrated")

    html = get_collection(
        client, reader, min_rating=min_rating, ordering="title"
    ).content.decode()

    assert card_titles(html) == expected


def test_filters_search_and_sort_combine(client, reader, other):
    tolkien = {"authors": "J.R.R. Tolkien", "status": "reading"}
    save_book(reader, "The Two Towers", rating=4, **tolkien)
    save_book(reader, "The Hobbit", rating=5, **tolkien)
    save_book(reader, "The Fellowship of the Ring", rating=5, **tolkien)
    save_book(reader, "The Silmarillion", rating=3, **tolkien)  # rating too low
    save_book(reader, "Unfinished Tales", rating=5, authors="J.R.R. Tolkien")  # status
    save_book(reader, "Dune", rating=5, status="reading")  # search
    save_book(other, "The Children of Hurin", rating=5, **tolkien)  # not the reader's

    html = get_collection(
        client, reader, status="reading", min_rating="4", q="tolkien", ordering="title"
    ).content.decode()

    assert card_titles(html) == [
        "The Fellowship of the Ring",
        "The Hobbit",
        "The Two Towers",
    ]


# --- Sorting ----------------------------------------------------------------


def test_default_sort_is_recently_added(client, reader):
    save_book(reader, "First")
    save_book(reader, "Second")
    save_book(reader, "Third")

    html = get_collection(client, reader).content.decode()

    assert card_titles(html) == ["Third", "Second", "First"]
    assert '<option value="-created_at" selected>' in html


def test_recently_updated_sort(client, reader):
    first = save_book(reader, "First")
    save_book(reader, "Second")
    first.notes = "Edited last"
    first.save()

    html = get_collection(client, reader, ordering="-updated_at").content.decode()

    assert card_titles(html) == ["First", "Second"]


def test_title_sort_ignores_case(client, reader):
    save_book(reader, "dune")
    save_book(reader, "Emma")
    save_book(reader, "Brave New World")

    html = get_collection(client, reader, ordering="title").content.decode()

    assert card_titles(html) == ["Brave New World", "dune", "Emma"]


def test_author_sort_puts_unknown_authors_last_then_sorts_by_title(client, reader):
    save_book(reader, "Unknown", authors="")
    save_book(reader, "Persuasion", authors="Jane Austen")
    save_book(reader, "Dune", authors="frank herbert")
    save_book(reader, "Emma", authors="Jane Austen")

    html = get_collection(client, reader, ordering="authors").content.decode()

    assert card_titles(html) == ["Dune", "Emma", "Persuasion", "Unknown"]


def test_sort_dropdown_offers_six_orderings(client, reader):
    html = get_collection(client, reader).content.decode()

    for value in (
        "-created_at",
        "-updated_at",
        "title",
        "authors",
        "-rating",
        "-first_publish_year",
    ):
        assert f'<option value="{value}"' in html


# --- Pagination ---------------------------------------------------------------


def make_books(owner, count, **fields):
    for n in range(count):
        save_book(owner, f"Book {n:02d}", **fields)


def test_collection_shows_twenty_books_per_page(client, reader):
    make_books(reader, 25)

    first = get_collection(client, reader).content.decode()
    second = get_collection(client, reader, page="2").content.decode()

    assert len(card_titles(first)) == 20
    assert len(card_titles(second)) == 5
    assert "Showing 21–25 of 25" in second


def test_filter_form_has_no_page_field_so_changes_start_at_page_one(client, reader):
    make_books(reader, 25, status="reading")
    make_books(reader, 25, status="finished")

    on_page_two = get_collection(client, reader, page="2").content.decode()
    # A filter change submits the form, which carries only the filter fields.
    after_filter = get_collection(client, reader, status="reading").content.decode()

    assert 'name="page"' not in on_page_two
    assert len(card_titles(after_filter)) == 20
    assert 'aria-current="page">1<' in after_filter
    assert 'rel="prev"' not in after_filter


@pytest.mark.parametrize("page", ["99", "0", "-1"])
def test_out_of_range_page_shows_the_last_page(client, reader, page):
    # Django's get_page: any whole number outside the range gives the last page.
    make_books(reader, 25)

    html = get_collection(client, reader, page=page).content.decode()

    assert len(card_titles(html)) == 5
    assert 'aria-current="page">2<' in html


@pytest.mark.parametrize("page", ["abc", "", "1.5"])
def test_invalid_page_shows_the_first_page(client, reader, page):
    make_books(reader, 25)

    html = get_collection(client, reader, page=page).content.decode()

    assert len(card_titles(html)) == 20
    assert 'aria-current="page">1<' in html


def test_single_page_has_no_page_links(client, reader):
    make_books(reader, 3)

    html = get_collection(client, reader).content.decode()

    assert "Showing 1–3 of 3" in html
    assert 'rel="next"' not in html
    assert 'rel="prev"' not in html


# --- Fallbacks and empty state -------------------------------------------------


def test_unknown_filter_and_sort_values_fall_back_to_defaults(client, reader):
    save_book(reader, "Older", status="reading", rating=2)
    save_book(reader, "Newer", status="finished")

    html = get_collection(
        client, reader, status="on_hold", min_rating="9", ordering="password"
    ).content.decode()

    assert card_titles(html) == ["Newer", "Older"]
    assert '<option value="-created_at" selected>' in html
    assert 'name="status" value="" class="sr-only" checked' in html
    assert 'name="min_rating" value="" class="sr-only" checked' in html


@pytest.mark.parametrize("min_rating", ["abc", "0", "-3", "4.5"])
def test_invalid_min_rating_means_any_rating(client, reader, min_rating):
    save_book(reader, "Unrated")

    html = get_collection(client, reader, min_rating=min_rating).content.decode()

    assert card_titles(html) == ["Unrated"]


def test_no_matches_shows_empty_state_with_clear_filters(client, reader):
    save_book(reader, "Dune")

    html = get_collection(client, reader, q="zzz").content.decode()

    assert card_titles(html) == []
    assert "No books match these filters" in html
    assert re.search(
        rf'<a href="{reverse("books:collection")}"[^>]*data-clear-filters', html
    )
    assert "data-empty-collection" not in html


def test_reset_filters_link_goes_to_the_unfiltered_collection(client, reader):
    html = get_collection(client, reader, q="x", status="reading").content.decode()

    assert re.search(
        rf'<a href="{reverse("books:collection")}"[^>]*data-reset-filters', html
    )


# --- HTMX ------------------------------------------------------------------------


def test_normal_request_returns_the_full_page(client, reader):
    save_book(reader, "Dune")

    response = get_collection(client, reader)
    html = response.content.decode()

    assert "<html" in html
    assert 'id="collection"' in html
    assert "HX-Request" in response["Vary"]


def test_htmx_request_returns_only_the_collection_fragment(client, reader):
    save_book(reader, "Dune", status="reading")
    client.force_login(reader)

    response = client.get(
        reverse("books:collection"),
        {"status": "reading"},
        headers={"HX-Request": "true"},
    )
    html = response.content.decode()

    assert response.status_code == 200
    assert "<html" not in html
    assert "navbar" not in html
    assert 'id="collection"' in html
    assert card_titles(html) == ["Dune"]
    assert 'data-status-count="reading">1<' in html
    assert "HX-Request" in response["Vary"]


def test_htmx_history_restore_gets_the_full_page(client, reader):
    client.force_login(reader)

    response = client.get(
        reverse("books:collection"),
        headers={"HX-Request": "true", "HX-History-Restore-Request": "true"},
    )

    assert "<html" in response.content.decode()


def test_collection_form_works_without_javascript_and_pushes_urls_with_htmx(
    client, reader
):
    make_books(reader, 25)
    url = reverse("books:collection")

    html = get_collection(client, reader).content.decode()
    form = re.search(r'<form id="collection"[^>]*>', html).group()

    # Without JavaScript: an ordinary GET form back to this page.
    assert 'method="get"' in form
    assert f'action="{url}"' in form
    # With HTMX: fetch the fragment, swap the whole area, and push the URL.
    assert f'hx-get="{url}"' in form
    assert 'hx-target="#collection"' in form
    assert 'hx-swap="outerHTML"' in form
    assert 'hx-push-url="true"' in form
    # Typing waits for Enter; emptying a search that was applied (X button or
    # deleting the text) refreshes right away. Selects and radios update on change.
    assert (
        "hx-trigger=\"change[target.type !== 'search'], submit, "
        "input[target.type === 'search' &amp;&amp; target.value === '' "
        "&amp;&amp; target.defaultValue !== '']\"" in form
    )
    # The search box keeps an id so HTMX restores focus to it after a swap.
    assert re.search(r'<input type="search" id="collection-search" name="q"', html)
    # Page links swap the same area (they inherit the form's target and push).
    assert re.search(r'<a href="\?page=2" hx-get="\?page=2" rel="next"', html)
