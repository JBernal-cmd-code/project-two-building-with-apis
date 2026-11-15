"""The SavedBook model: one row per user per saved book.

Book facts from Open Library are copied onto the row (there is no shared
catalog table), so the collection keeps working when Open Library is down.
Validation rules live here so the website and the API behave the same.
"""

import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

COVER_URL = "https://covers.openlibrary.org/b/id/{cover_id}-M.jpg"

WORK_KEY_PREFIX = "/works/"
WORK_KEY_PATTERN = re.compile(r"OL\d+W")


def normalize_work_key(value):
    """Strip whitespace and a leading ``/works/`` from an Open Library key."""
    if not isinstance(value, str):
        return value
    value = value.strip()
    return value.removeprefix(WORK_KEY_PREFIX)


def validate_work_key(value):
    """Shared work key rule: ``OL`` + digits + ``W``, prefix allowed."""
    if not WORK_KEY_PATTERN.fullmatch(normalize_work_key(value) or ""):
        raise ValidationError(
            "Enter a valid Open Library work key, like OL27482W.",
            code="invalid_work_key",
        )


class WorkKeyField(models.CharField):
    """A CharField that always stores the short ``OL…W`` form."""

    def to_python(self, value):
        return normalize_work_key(super().to_python(value))

    def pre_save(self, model_instance, add):
        value = normalize_work_key(getattr(model_instance, self.attname))
        setattr(model_instance, self.attname, value)
        return value


def validate_not_blank(value):
    if not value or not value.strip():
        raise ValidationError("This field cannot be blank.", code="blank")


class SavedBook(models.Model):
    class Status(models.TextChoices):
        WANT_TO_READ = "want_to_read", "Want to read"
        READING = "reading", "Reading"
        FINISHED = "finished", "Finished"
        ABANDONED = "abandoned", "Did not finish"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_books",
    )

    # Book facts: set at creation, read-only afterward.
    ol_work_key = WorkKeyField(
        "Open Library work key", max_length=32, validators=[validate_work_key]
    )
    title = models.CharField(max_length=500, validators=[validate_not_blank])
    authors = models.CharField(max_length=1000, blank=True)
    first_publish_year = models.IntegerField(null=True, blank=True)
    cover_id = models.PositiveIntegerField(null=True, blank=True)

    # Reading-tracking fields: editable.
    total_pages = models.PositiveIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1)]
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.WANT_TO_READ
    )
    current_page = models.PositiveIntegerField(default=0)
    rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = (
            models.UniqueConstraint(
                fields=("owner", "ol_work_key"),
                name="unique_saved_book_per_owner",
                violation_error_message="This book is already in your collection.",
            ),
        )

    def __str__(self):
        return self.title

    @property
    def authors_display(self):
        return self.authors or "Unknown author"

    @property
    def cover_url(self):
        if self.cover_id is None:
            return ""
        return COVER_URL.format(cover_id=self.cover_id)

    @property
    def progress_percent(self):
        """Whole-number percent read, or None when total pages is unknown."""
        if not self.total_pages:
            return None
        return min(100, round(self.current_page * 100 / self.total_pages))

    @property
    def shows_progress(self):
        """Cards show progress only when there is some to show."""
        return (
            self.total_pages is not None
            and self.current_page > 0
            and self.status != self.Status.WANT_TO_READ
        )

    def _apply_finished_autofill(self):
        # Finished auto-fill: a finished book with a known length shows 100%.
        if self.status == self.Status.FINISHED and self.total_pages:
            self.current_page = self.total_pages

    def save(self, *args, **kwargs):
        self._apply_finished_autofill()
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        self._apply_finished_autofill()
        if (
            self.total_pages
            and self.current_page is not None
            and self.current_page > self.total_pages
        ):
            raise ValidationError(
                {"current_page": "Current page can't be more than total pages."}
            )
