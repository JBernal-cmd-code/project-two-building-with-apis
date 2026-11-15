"""Website forms for saved books."""

from django import forms

from .models import SavedBook

RATING_CHOICES = [("", "Unrated")] + [
    (n, f"{n} star{'s' if n > 1 else ''}") for n in range(1, 6)
]


class SavedBookEditForm(forms.ModelForm):
    """Only the reading-tracking fields; book facts are locked after creation."""

    rating = forms.TypedChoiceField(
        choices=RATING_CHOICES, coerce=int, empty_value=None, required=False
    )

    class Meta:
        model = SavedBook
        fields = ("status", "current_page", "total_pages", "rating", "notes")
