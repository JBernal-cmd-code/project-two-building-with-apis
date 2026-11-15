from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect, render


class LoginView(auth_views.LoginView):
    """Django's login plus a "Welcome back" flash message."""

    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Welcome back, {form.get_user().username}!")
        return response


class LogoutView(auth_views.LogoutView):
    """Django's logout (POST only) plus a confirmation flash message."""

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        messages.info(request, "You've been logged out.")
        return response


def signup(request):
    """Create an account with a username and password, then log the user in."""
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(
                request, f"Welcome, {user.username}! Your collection is ready."
            )
            return redirect(settings.LOGIN_REDIRECT_URL)
    else:
        form = UserCreationForm()

    return render(request, "accounts/signup.html", {"form": form})
