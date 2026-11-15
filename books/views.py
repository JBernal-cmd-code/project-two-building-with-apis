"""Website views for saved books.

Phase 1 placeholders. The real collection page arrives in Phase 2 and the
search page in Phase 4.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def collection(request):
    return render(request, "books/placeholder.html", {"page_title": "My Collection"})


@login_required
def search(request):
    return render(request, "books/placeholder.html", {"page_title": "Find books"})
