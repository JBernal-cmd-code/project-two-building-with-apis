"""The app's own REST API for saved books. Never calls Open Library.

The list accepts the same ``q``, ``status``, ``min_rating``, ``ordering``,
and ``page`` parameters as My Collection, with the same fallbacks.
"""

from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination

from .collection_query import PAGE_SIZE, CollectionParams, collection_books
from .serializers import DUPLICATE_MESSAGE, SavedBookSerializer


class CollectionPagination(PageNumberPagination):
    """20 per page, with the website's safe page lookup.

    An out-of-range page shows the last page and an invalid one shows page 1,
    instead of DRF's default 404.
    """

    page_size = PAGE_SIZE

    def paginate_queryset(self, queryset, request, view=None):
        self.request = request
        self.page = Paginator(queryset, self.page_size).get_page(
            request.query_params.get(self.page_query_param)
        )
        return list(self.page)


class SavedBookViewSet(viewsets.ModelViewSet):
    serializer_class = SavedBookSerializer
    pagination_class = CollectionPagination

    def get_queryset(self):
        # Privacy: every query starts from the current user's books, so another
        # user's book is a 404 for every method.
        books = self.request.user.saved_books.all()
        if self.action == "list":
            params = CollectionParams.from_query(self.request.query_params)
            books = collection_books(books, params)
        return books

    def perform_create(self, serializer):
        try:
            with transaction.atomic():
                serializer.save(owner=self.request.user)
        except IntegrityError:  # the same book created twice at once
            raise ValidationError(DUPLICATE_MESSAGE) from None
