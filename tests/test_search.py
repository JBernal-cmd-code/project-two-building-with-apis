"""The Find books page (/books/search/), with Open Library faked."""

import pytest
import requests
from django.urls import reverse

from books.models import SavedBook

pytestmark = pytest.mark.django_db

PASSWORD = "a-Long-unusual-pass-42"

HOBBIT_DOC = {
    "key": "/works/OL27482W",
    "title": "The Hobbit",
    "author_name": ["J.R.R. Tolkien"],
    "first_publish_year": 1937,
    "cover_i": 14627509,
    "number_of_pages_median": 310,
}
DUNE_DOC = {
    "key": "/works/OL893415W",
    "title": "Dune",
    "author_name": ["Frank Herbert"],
    "first_publish_year": 1965,
}


@pytest.fixture
def reader(django_user_model):
    return django_user_model.objects.create_user(username="reader", password=PASSWORD)


@pytest.fixture
def other(django_user_model):
    return django_user_model.objects.create_user(username="other", password=PASSWORD)


def search_page(client, user, query):
    client.force_login(user)
    response = client.get(reverse("books:search"), {"q": query})
    return response, response.content.decode()


def test_search_requires_login(client):
    url = reverse("books:search")

    response = client.get(url)

    assert response.status_code == 302
    assert response.url == f"{reverse('accounts:login')}?next={url}"


@pytest.mark.parametrize(
    ("query", "fake"),
    [
        ("", None),
        ("the hobbit", {"body": {"numFound": 1, "docs": [HOBBIT_DOC]}}),
        ("the hobbit", {"error": requests.Timeout()}),
    ],
    ids=["empty", "results", "error"],
)
def test_search_page_is_never_cached(client, reader, fake_open_library, query, fake):
    # Back after a save must reload the page, not show the pre-save copy.
    if fake:
        fake_open_library(**fake)

    response, _ = search_page(client, reader, query)

    cache_control = response.headers["Cache-Control"]
    assert "no-cache" in cache_control
    assert "no-store" in cache_control
    assert "must-revalidate" in cache_control


def test_empty_query_shows_form_without_calling_open_library(client, reader):
    # The network guard fails this test if Open Library is called.
    response, html = search_page(client, reader, "")

    assert response.status_code == 200
    assert 'name="q"' in html
    assert "data-search-result" not in html
    assert "data-no-matches" not in html


def test_results_render_with_cover_title_author_and_year(
    client, reader, fake_open_library
):
    calls = fake_open_library({"numFound": 2, "docs": [HOBBIT_DOC, DUNE_DOC]})

    response, html = search_page(client, reader, "  the hobbit  ")

    assert response.status_code == 200
    assert calls[0]["params"]["q"] == "the hobbit"
    assert html.count("data-search-result") == 2
    assert "The Hobbit" in html
    assert "J.R.R. Tolkien" in html
    assert "First published 1937" in html
    assert 'src="https://covers.openlibrary.org/b/id/14627509-M.jpg"' in html
    # Dune has no cover in the fake response, so it gets the placeholder.
    assert "data-cover-placeholder" in html


def test_results_show_total_matches_and_refine_tip(client, reader, fake_open_library):
    fake_open_library({"numFound": 1234, "docs": [HOBBIT_DOC]})

    _, html = search_page(client, reader, "the hobbit")

    assert "Found 1,234 matches" in html
    assert "showing the top 1" in html
    assert "Not seeing your book?" in html


def test_no_matches_shows_message(client, reader, fake_open_library):
    fake_open_library({"numFound": 0, "docs": []})

    _, html = search_page(client, reader, "asdkjhqwe")

    assert "data-no-matches" in html
    assert "No books matched" in html
    assert "asdkjhqwe" in html
    assert "data-search-summary" not in html


def test_save_form_carries_book_facts_and_return_url(client, reader, fake_open_library):
    fake_open_library({"numFound": 1, "docs": [HOBBIT_DOC]})

    _, html = search_page(client, reader, "the hobbit")

    assert f'hx-post="{reverse("books:save")}"' in html
    assert 'name="csrfmiddlewaretoken"' in html
    for name, value in [
        ("ol_work_key", "OL27482W"),
        ("title", "The Hobbit"),
        ("authors", "J.R.R. Tolkien"),
        ("first_publish_year", "1937"),
        ("cover_id", "14627509"),
        ("total_pages", "310"),
        ("next", "/books/search/?q=the+hobbit"),
    ]:
        assert f'name="{name}" value="{value}"' in html


def test_result_text_is_escaped(client, reader, fake_open_library):
    doc = HOBBIT_DOC | {"title": '<script>alert("x")</script>'}
    fake_open_library({"numFound": 1, "docs": [doc]})

    _, html = search_page(client, reader, "x")

    assert "<script>alert" not in html
    assert "&lt;script&gt;" in html


@pytest.mark.parametrize(
    ("fake", "message"),
    [
        ({"error": requests.Timeout()}, "took too long to respond"),
        ({"error": requests.ConnectionError()}, "Could not connect to Open Library"),
        ({"status": 429}, "too many requests"),
        ({"status": 503}, "having problems right now"),
        ({"status": 404}, "unexpected error"),
        ({"raw": b"not json"}, "could not read"),
        ({"body": {"unexpected": "shape"}}, "could not read"),
        ({"error": requests.TooManyRedirects()}, "Something went wrong"),
    ],
)
def test_each_error_shows_alert_query_and_collection_link(
    client, reader, fake_open_library, fake, message
):
    fake_open_library(**fake)

    response, html = search_page(client, reader, "dune")

    assert response.status_code == 200
    assert "data-search-error" in html
    assert message in html
    assert 'value="dune"' in html
    assert f'href="{reverse("books:collection")}"' in html
    assert "data-search-result" not in html


def test_owned_results_show_badge_linking_to_saved_book_instead_of_save(
    client, reader, other, fake_open_library
):
    mine = SavedBook.objects.create(
        owner=reader, ol_work_key="OL27482W", title="The Hobbit"
    )
    # Another user owning Dune must not mark Dune as owned for the reader.
    SavedBook.objects.create(owner=other, ol_work_key="OL893415W", title="Dune")
    fake_open_library({"numFound": 2, "docs": [HOBBIT_DOC, DUNE_DOC]})

    _, html = search_page(client, reader, "fantasy")

    hobbit_card, dune_card = html.split("data-search-result")[1:]
    assert "In your collection" in hobbit_card
    assert f'href="{mine.get_absolute_url()}"' in hobbit_card
    assert "data-save-form" not in hobbit_card
    assert "data-save-form" in dune_card
    assert "In your collection" not in dune_card


def test_owned_result_cover_and_title_open_the_saved_book(
    client, reader, fake_open_library
):
    mine = SavedBook.objects.create(
        owner=reader, ol_work_key="OL27482W", title="The Hobbit"
    )
    fake_open_library({"numFound": 1, "docs": [HOBBIT_DOC]})

    _, html = search_page(client, reader, "the hobbit")

    card = html.split("data-search-result")[1]
    link = card.split("data-owned-link>")[1].split("</a>")[0]
    assert f'href="{mine.get_absolute_url()}"' in card.split("data-owned-link>")[0]
    assert "14627509-M.jpg" in link  # the cover
    assert "The Hobbit</h3>" in link  # the title
    assert "data-openlibrary-link" not in card


def test_unsaved_result_title_opens_open_library_in_new_tab(
    client, reader, fake_open_library
):
    fake_open_library({"numFound": 1, "docs": [HOBBIT_DOC]})

    _, html = search_page(client, reader, "the hobbit")

    card = html.split("data-search-result")[1]
    before, link = card.split("data-openlibrary-link>")
    link = link.split("</a>")[0]
    assert (
        '<a href="https://openlibrary.org/works/OL27482W" target="_blank" '
        'rel="noopener noreferrer"'
    ) in before
    assert "14627509-M.jpg" in link  # the cover
    assert "The Hobbit<" in link  # the title
    assert "data-owned-link" not in card
    # A save response swaps this block out of band by this id.
    assert '<div id="result-head-OL27482W">' in card


def test_open_library_failure_shows_friendly_alert_and_keeps_query(
    client, reader, fake_open_library
):
    fake_open_library(error=requests.Timeout())
    # See an unhandled error the way a user would: as a 500 page.
    client.raise_request_exception = False

    response, html = search_page(client, reader, "the hobbit")

    assert response.status_code == 200
    assert "data-search-error" in html
    assert "Open Library took too long to respond" in html
    assert 'value="the hobbit"' in html
    assert f'href="{reverse("books:collection")}"' in html
    assert "saved books are still available" in html
