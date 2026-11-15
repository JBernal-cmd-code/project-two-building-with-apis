"""Book detail page: viewing, editing, and removing one saved book."""

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


def save_book(owner, **fields):
    data = {"ol_work_key": "OL27482W", "title": "The Hobbit"} | fields
    return SavedBook.objects.create(owner=owner, **data)


def test_another_users_book_is_not_found_on_view_edit_and_delete(client, reader, other):
    book = save_book(reader, status="reading", current_page=10, total_pages=300)
    client.force_login(other)
    detail_url = reverse("books:detail", args=[book.pk])
    delete_url = reverse("books:delete", args=[book.pk])

    view = client.get(detail_url)
    edit = client.post(
        detail_url, {"status": "finished", "current_page": 0, "total_pages": 300}
    )
    remove = client.post(delete_url)

    assert view.status_code == 404
    assert edit.status_code == 404
    assert remove.status_code == 404
    book.refresh_from_db()
    assert book.status == "reading"
    assert book.current_page == 10


def test_edit_saves_tracking_fields_and_ignores_posted_book_facts(client, reader):
    book = save_book(
        reader,
        ol_work_key="OL27482W",
        title="The Hobbit",
        authors="J.R.R. Tolkien",
        first_publish_year=1937,
        cover_id=14627509,
    )
    client.force_login(reader)

    client.post(
        reverse("books:detail", args=[book.pk]),
        {
            "status": "reading",
            "current_page": 42,
            "total_pages": 310,
            "rating": 4,
            "notes": "Loving it.",
            # Book facts are locked after creation; these must be ignored.
            "ol_work_key": "OL1W",
            "title": "Changed",
            "authors": "Someone Else",
            "first_publish_year": 2001,
            "cover_id": 1,
        },
    )

    book.refresh_from_db()
    assert (book.status, book.current_page, book.total_pages) == ("reading", 42, 310)
    assert (book.rating, book.notes) == (4, "Loving it.")
    assert book.ol_work_key == "OL27482W"
    assert book.title == "The Hobbit"
    assert book.authors == "J.R.R. Tolkien"
    assert book.first_publish_year == 1937
    assert book.cover_id == 14627509


def test_delete_requires_post_then_removes_and_confirms(client, reader):
    book = save_book(reader, title="The Hobbit")
    client.force_login(reader)
    url = reverse("books:delete", args=[book.pk])

    get_response = client.get(url)

    assert get_response.status_code == 405
    assert SavedBook.objects.filter(pk=book.pk).exists()

    response = client.post(url, follow=True)

    assert response.redirect_chain == [(reverse("books:collection"), 302)]
    assert not SavedBook.objects.filter(pk=book.pk).exists()
    assert (
        "Removed &#x27;The Hobbit&#x27; from your collection."
        in response.content.decode()
    )


def detail_url(book):
    return reverse("books:detail", args=[book.pk])


def test_detail_requires_login(client, reader):
    book = save_book(reader)
    url = detail_url(book)

    response = client.get(url)

    assert response.status_code == 302
    assert response.url == f"{reverse('accounts:login')}?next={url}"


def test_owner_sees_book_facts_tracking_and_edit_form(client, reader):
    book = save_book(
        reader,
        title="The Hobbit",
        authors="J.R.R. Tolkien",
        first_publish_year=1937,
        cover_id=14627509,
        status="reading",
        current_page=155,
        total_pages=310,
        rating=4,
    )
    client.force_login(reader)

    response = client.get(detail_url(book))

    html = response.content.decode()
    assert response.status_code == 200
    assert "The Hobbit" in html
    assert "J.R.R. Tolkien" in html
    assert "1937" in html
    assert 'src="https://covers.openlibrary.org/b/id/14627509-M.jpg"' in html
    assert "badge-info" in html and "Reading" in html
    assert 'aria-label="4 of 5 stars"' in html
    assert "Page 155 of 310" in html and "50%" in html
    for name in ("status", "current_page", "total_pages", "rating", "notes"):
        assert f'name="{name}"' in html
    for locked in ("ol_work_key", "title", "authors", "first_publish_year", "cover_id"):
        assert f'name="{locked}"' not in html


def test_book_without_cover_shows_placeholder_on_detail(client, reader):
    book = save_book(reader, cover_id=None)
    client.force_login(reader)

    html = client.get(detail_url(book)).content.decode()

    assert "data-cover-placeholder" in html
    assert "<img" not in html


def test_collection_cards_link_to_detail_page(client, reader):
    book = save_book(reader)
    client.force_login(reader)

    html = client.get(reverse("books:collection")).content.decode()

    assert f'href="{detail_url(book)}"' in html


def test_valid_edit_redirects_with_saved_message(client, reader):
    book = save_book(reader)
    client.force_login(reader)

    response = client.post(
        detail_url(book),
        {"status": "reading", "current_page": 12, "total_pages": "", "rating": ""},
        follow=True,
    )

    assert response.redirect_chain == [(detail_url(book), 302)]
    assert [str(m) for m in response.context["messages"]] == ["Saved"]
    book.refresh_from_db()
    assert (book.status, book.current_page, book.total_pages, book.rating) == (
        "reading",
        12,
        None,
        None,
    )


@pytest.mark.parametrize(
    ("changes", "field", "error"),
    [
        (
            {"current_page": 400, "total_pages": 300},
            "current_page",
            "Current page can&#x27;t be more than total pages.",
        ),
        ({"rating": 6}, "rating", "Select a valid choice."),
        ({"rating": 0}, "rating", "Select a valid choice."),
        ({"total_pages": 0}, "total_pages", "greater than or equal to 1"),
        ({"current_page": -1}, "current_page", "greater than or equal to 0"),
        ({"status": "on_hold"}, "status", "Select a valid choice."),
    ],
)
def test_invalid_edit_shows_field_error_and_does_not_save(
    client, reader, changes, field, error
):
    book = save_book(
        reader, status="reading", current_page=10, total_pages=300, rating=3
    )
    client.force_login(reader)
    data = {
        "status": "reading",
        "current_page": 10,
        "total_pages": 300,
        "rating": 3,
        "notes": "edited",
    } | changes

    response = client.post(detail_url(book), data)

    assert response.status_code == 200
    assert field in response.context["form"].errors
    assert error in response.content.decode()
    book.refresh_from_db()
    assert (book.status, book.current_page, book.total_pages, book.rating) == (
        "reading",
        10,
        300,
        3,
    )
    assert book.notes == ""


def test_marking_finished_through_the_form_fills_current_page(client, reader):
    book = save_book(reader, status="reading", current_page=40, total_pages=310)
    client.force_login(reader)

    client.post(
        detail_url(book),
        {"status": "finished", "current_page": 40, "total_pages": 310},
    )

    book.refresh_from_db()
    assert (book.status, book.current_page) == ("finished", 310)


def test_notes_with_html_are_shown_escaped(client, reader):
    book = save_book(reader, notes='<script>alert("x")</script> <b>bold</b>')
    client.force_login(reader)

    html = client.get(detail_url(book)).content.decode()

    assert "<script>alert" not in html
    assert "<b>bold</b>" not in html
    assert "&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;" in html
    assert "&lt;b&gt;bold&lt;/b&gt;" in html


def test_remove_button_opens_confirmation_dialog_posting_to_delete(client, reader):
    book = save_book(reader)
    client.force_login(reader)

    html = client.get(detail_url(book)).content.decode()

    assert '<dialog id="remove_modal"' in html
    assert "status, rating, and notes" in html
    assert (
        f'<form method="post" action="{reverse("books:delete", args=[book.pk])}">'
        in html
    )
