"""Display helpers for book cards: status colors and star ratings.

Class names are written out in full here so Tailwind's scan of this file
picks them up.
"""

from django import template

from books.models import SavedBook

register = template.Library()

STATUS_STYLES = {
    SavedBook.Status.WANT_TO_READ: {"badge": "badge-secondary", "dot": "bg-secondary"},
    SavedBook.Status.READING: {"badge": "badge-info", "dot": "bg-info"},
    SavedBook.Status.FINISHED: {"badge": "badge-success", "dot": "bg-success"},
    SavedBook.Status.ABANDONED: {"badge": "badge-warning", "dot": "bg-warning"},
}


@register.inclusion_tag("books/_status_badge.html")
def status_badge(book, size="badge-xs"):
    return {
        "label": book.get_status_display(),
        "style": STATUS_STYLES[book.status],
        "size": size,
    }


@register.filter
def status_dot(status):
    """The colored dot class for a status value, as used in the sidebar."""
    return STATUS_STYLES[status]["dot"]


@register.simple_tag(takes_context=True)
def page_url(context, number):
    """The current query string with only ``page`` changed."""
    query = context["request"].GET.copy()
    query["page"] = number
    return "?" + query.urlencode()


@register.inclusion_tag("books/_stars.html")
def stars(rating, size="text-xs"):
    """Filled and empty stars; renders nothing for an unrated book."""
    rating = rating or 0
    return {
        "rating": rating,
        "filled": "★" * rating,
        "empty": "★" * (5 - rating),
        "size": size,
    }
