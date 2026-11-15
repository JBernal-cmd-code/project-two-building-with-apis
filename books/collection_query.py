"""Search, filter, and sort a user's saved books from query parameters.

Shared by the My Collection page and (in Phase 6) the API list, so both
accept the same ``q``, ``status``, ``min_rating``, and ``ordering`` values
and fall back to the same defaults when a value is unknown.
"""

from dataclasses import dataclass

from django.db.models import Case, Count, F, Q, When
from django.db.models.functions import Lower

from .models import SavedBook

PAGE_SIZE = 20

DEFAULT_ORDERING = "-created_at"
ORDERING_LABELS = {
    "-created_at": "Recently added",
    "-updated_at": "Recently updated",
    "title": "Title (A–Z)",
    "authors": "Author (A–Z)",
    "-rating": "Rating (high to low)",
    "-first_publish_year": "Publish year (newest)",
}

MIN_RATING_CHOICES = (5, 4, 3, 2, 1)


@dataclass(frozen=True)
class CollectionParams:
    """Cleaned collection parameters; unknown values become defaults."""

    q: str = ""
    status: str = ""
    min_rating: int | None = None
    ordering: str = DEFAULT_ORDERING

    @classmethod
    def from_query(cls, data):
        status = data.get("status", "")
        ordering = data.get("ordering", "")
        return cls(
            q=data.get("q", "").strip(),
            status=status if status in SavedBook.Status.values else "",
            min_rating=_parse_rating(data.get("min_rating", "")),
            ordering=ordering if ordering in ORDERING_LABELS else DEFAULT_ORDERING,
        )

    @property
    def is_filtered(self):
        return bool(self.q or self.status or self.min_rating)


def _parse_rating(value):
    try:
        rating = int(value)
    except TypeError, ValueError:
        return None
    return rating if rating in MIN_RATING_CHOICES else None


def filter_books(books, params, *, by_status=True):
    """Apply search and rating filters, plus the status filter unless told not to."""
    if params.q:
        books = books.filter(
            Q(title__icontains=params.q) | Q(authors__icontains=params.q)
        )
    if params.min_rating:
        books = books.filter(rating__gte=params.min_rating)
    if by_status and params.status:
        books = books.filter(status=params.status)
    return books


def status_counts(books, params):
    """Books per status, plus ``all``, with every filter except status applied.

    The counts match what clicking each status would show.
    """
    return filter_books(books, params, by_status=False).aggregate(
        all=Count("pk"),
        **{
            value: Count("pk", filter=Q(status=value))
            for value in SavedBook.Status.values
        },
    )


TITLE = Lower("title").asc()

# Every ordering ends with the title (case-insensitive) to break ties.
# Empty ratings, years, and authors sort last.
ORDERINGS = {
    "-created_at": (F("created_at").desc(), TITLE),
    "-updated_at": (F("updated_at").desc(), TITLE),
    "title": (TITLE, F("pk").asc()),
    "authors": (
        Case(When(authors="", then=1), default=0).asc(),
        Lower("authors").asc(),
        TITLE,
    ),
    "-rating": (F("rating").desc(nulls_last=True), TITLE),
    "-first_publish_year": (F("first_publish_year").desc(nulls_last=True), TITLE),
}


def order_books(books, ordering):
    return books.order_by(*ORDERINGS[ordering])


def collection_books(books, params):
    """The filtered, ordered books for one collection view."""
    return order_books(filter_books(books, params), params.ordering)
