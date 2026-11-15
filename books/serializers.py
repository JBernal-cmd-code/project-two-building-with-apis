"""API serializers for saved books.

Validation matches the website: field rules come from the model's
validators, and the model's ``clean()`` adds the page rule and Finished
auto-fill.
"""

import copy

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import SavedBook, normalize_work_key

DUPLICATE_MESSAGE = "This book is already in your collection."

# Book facts: writable on create, read-only (silently ignored) on update.
LOCKED_FIELDS = ("ol_work_key", "title", "authors", "first_publish_year", "cover_id")


class SavedBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedBook
        fields = (
            "id",
            *LOCKED_FIELDS,
            "status",
            "current_page",
            "total_pages",
            "rating",
            "notes",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")

    def get_fields(self):
        fields = super().get_fields()
        if self.instance is not None:
            for name in LOCKED_FIELDS:
                fields[name].read_only = True
        return fields

    def validate_ol_work_key(self, value):
        # The model's validator already accepted the key with or without
        # ``/works/``; store and compare the short form.
        return normalize_work_key(value)

    def validate(self, attrs):
        if self.instance is None:
            owner = self.context["request"].user
            # The owner is server-set, so DRF can't check owner + work key
            # uniqueness on its own. Check the current user's books instead.
            if owner.saved_books.filter(ol_work_key=attrs["ol_work_key"]).exists():
                raise serializers.ValidationError(DUPLICATE_MESSAGE)
            book = SavedBook(owner=owner, **attrs)
        else:
            # Check a copy so a rejected update leaves the instance untouched.
            book = copy.copy(self.instance)
            for name, value in attrs.items():
                setattr(book, name, value)
        try:
            book.clean()
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.message_dict) from None
        return attrs
