"""Website views for saved books.

My Collection, book detail, edit, and remove use only local data and never
call Open Library. The search page is still a placeholder until Phase 4.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from . import openlibrary
from .forms import SavedBookCreateForm, SavedBookEditForm


@login_required
def collection(request):
    # Privacy: every query starts from the current user's books.
    books = request.user.saved_books.all()
    return render(request, "books/collection.html", {"books": books})


def get_own_book(request, pk):
    """Another user's book is indistinguishable from one that doesn't exist."""
    return get_object_or_404(request.user.saved_books, pk=pk)


@login_required
def detail(request, pk):
    book = get_own_book(request, pk)
    if request.method == "POST":
        form = SavedBookEditForm(request.POST, instance=book)
        if form.is_valid():
            form.save()
            messages.success(request, "Saved")
            return redirect(book)
        # Validation copied the rejected values onto the instance; show the
        # stored book in the header while the form keeps what was typed.
        book.refresh_from_db()
    else:
        form = SavedBookEditForm(instance=book)
    return render(request, "books/detail.html", {"book": book, "form": form})


@login_required
@require_POST
def delete(request, pk):
    book = get_own_book(request, pk)
    book.delete()
    messages.success(request, f"Removed '{book.title}' from your collection.")
    return redirect("books:collection")


@login_required
@never_cache
def search(request):
    """Search Open Library: the only view that calls it, once per search.

    Never cached, so Back after saving reloads the current owned/Save state
    instead of the copy from before the save.
    """
    query = request.GET.get("q", "").strip()
    context = {"query": query}
    if query:
        try:
            found = openlibrary.search(query)
        except openlibrary.OpenLibraryError as error:
            context["error"] = str(error)
            return render(request, "books/search.html", context)
        context["found"] = found
        # One lookup, starting from the user's own books, finds owned results.
        owned = {
            book.ol_work_key: book
            for book in request.user.saved_books.filter(
                ol_work_key__in=[result.work_key for result in found.results]
            )
        }
        context["items"] = [
            (result, owned.get(result.work_key)) for result in found.results
        ]
    return render(request, "books/search.html", context)


def _back_to_search(request):
    """Where a no-JavaScript save returns: the search it came from."""
    next_url = request.POST.get("next", "")
    if url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return redirect(next_url)
    return redirect("books:search")


@login_required
@require_POST
def save(request):
    """Save a search result from its posted facts. Never calls Open Library."""
    is_htmx = request.headers.get("HX-Request") == "true"
    form = SavedBookCreateForm(request.POST)
    if not form.is_valid():
        message = "Couldn't save this book. Try searching again."
        if not is_htmx:
            messages.error(request, message)
            return _back_to_search(request)
        # Re-render this card's Save form with a small inline error.
        posted = request.POST
        book = {
            "work_key": posted.get("ol_work_key", ""),
            "title": posted.get("title", ""),
            "authors": posted.get("authors", ""),
            "first_publish_year": posted.get("first_publish_year", ""),
            "cover_id": posted.get("cover_id", ""),
            "total_pages": posted.get("total_pages", ""),
        }
        return render(
            request,
            "books/_save_button.html",
            {"book": book, "save_error": message, "next": posted.get("next", "")},
        )

    # The owner is server-set, so the form can't check uniqueness; a book the
    # user already has counts as saved.
    work_key = form.cleaned_data["ol_work_key"]
    book = request.user.saved_books.filter(ol_work_key=work_key).first()
    if book is None:
        book = form.save(commit=False)
        book.owner = request.user
        try:
            with transaction.atomic():
                book.save()
        except IntegrityError:  # saved twice at once (a double click)
            book = request.user.saved_books.get(ol_work_key=work_key)
        created = True
    else:
        created = False

    if is_htmx:
        return render(request, "books/_save_success.html", {"saved": book})
    if created:
        messages.success(request, f"Saved '{book.title}' to your collection.")
    else:
        messages.info(request, f"'{book.title}' is already in your collection.")
    return _back_to_search(request)
