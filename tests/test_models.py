"""SavedBook model rules, shared by the website and the API."""

import pytest
from django.core.exceptions import ValidationError

from books.models import SavedBook

pytestmark = pytest.mark.django_db

PASSWORD = "a-Long-unusual-pass-42"


@pytest.fixture
def reader(django_user_model):
    return django_user_model.objects.create_user(username="reader", password=PASSWORD)


def make_book(owner, **fields):
    data = {"ol_work_key": "OL27482W", "title": "The Hobbit"} | fields
    return SavedBook(owner=owner, **data)


@pytest.mark.parametrize("raw", ["OL27482W", "/works/OL27482W"])
def test_work_key_is_stored_in_short_form(reader, raw):
    book = make_book(reader, ol_work_key=raw)

    book.full_clean()
    book.save()

    book.refresh_from_db()
    assert book.ol_work_key == "OL27482W"


@pytest.mark.parametrize(
    "bad_key",
    ["", "OL27482", "OL27482M", "ol27482w", "27482W", "/books/OL27482W", "OLW"],
)
def test_invalid_work_key_is_rejected(reader, bad_key):
    book = make_book(reader, ol_work_key=bad_key)

    with pytest.raises(ValidationError) as excinfo:
        book.full_clean()

    assert "ol_work_key" in excinfo.value.message_dict


def test_finished_sets_current_page_to_total_pages(reader):
    book = make_book(reader, total_pages=310, current_page=120)
    book.save()

    book.status = SavedBook.Status.FINISHED
    book.save()

    book.refresh_from_db()
    assert book.current_page == 310


def test_finished_without_total_pages_leaves_current_page_alone(reader):
    book = make_book(reader, current_page=120, status=SavedBook.Status.FINISHED)
    book.save()

    book.refresh_from_db()
    assert book.current_page == 120
    assert book.total_pages is None


def test_finished_corrects_an_overshooting_page_instead_of_rejecting(reader):
    book = make_book(
        reader, total_pages=300, current_page=500, status=SavedBook.Status.FINISHED
    )

    book.full_clean()

    assert book.current_page == 300


@pytest.mark.parametrize("title", ["", "   "])
def test_blank_or_whitespace_title_is_rejected(reader, title):
    book = make_book(reader, title=title)

    with pytest.raises(ValidationError) as excinfo:
        book.full_clean()

    assert "title" in excinfo.value.message_dict


@pytest.mark.parametrize("rating", [None, 1, 3, 5])
def test_rating_accepts_empty_and_one_to_five(reader, rating):
    make_book(reader, rating=rating).full_clean()


@pytest.mark.parametrize("rating", [0, 6])
def test_rating_outside_one_to_five_is_rejected(reader, rating):
    with pytest.raises(ValidationError) as excinfo:
        make_book(reader, rating=rating).full_clean()

    assert "rating" in excinfo.value.message_dict


def test_current_page_above_total_pages_is_rejected(reader):
    book = make_book(reader, total_pages=300, current_page=301)

    with pytest.raises(ValidationError) as excinfo:
        book.full_clean()

    assert "current_page" in excinfo.value.message_dict


def test_current_page_equal_to_total_or_without_total_is_allowed(reader):
    make_book(reader, total_pages=300, current_page=300).full_clean()
    make_book(reader, current_page=999).full_clean()


def test_total_pages_must_be_at_least_one(reader):
    with pytest.raises(ValidationError) as excinfo:
        make_book(reader, total_pages=0).full_clean()

    assert "total_pages" in excinfo.value.message_dict


def test_same_owner_cannot_save_the_same_work_twice(reader):
    make_book(reader).save()
    duplicate = make_book(reader, ol_work_key="/works/OL27482W")

    with pytest.raises(ValidationError) as excinfo:
        duplicate.full_clean()

    assert "This book is already in your collection." in str(excinfo.value)


def test_different_owners_can_save_the_same_work(reader, django_user_model):
    other = django_user_model.objects.create_user(username="other", password=PASSWORD)
    make_book(reader).save()

    make_book(other).full_clean()


def test_new_book_defaults_to_want_to_read_at_page_zero(reader):
    book = make_book(reader)
    book.save()

    assert book.status == SavedBook.Status.WANT_TO_READ
    assert book.get_status_display() == "Want to read"
    assert book.current_page == 0
    assert book.rating is None
