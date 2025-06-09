from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy


class SuperuserBypassMixin(UserPassesTestMixin):
    """
    A reusable mixin that allows superusers to bypass the `test_func` check.
    Subclasses must implement `user_test_func()`.
    """

    def test_func(self):
        user = self.request.user

        # Let the view decide on guests (don't block here)
        if user.is_authenticated and user.is_superuser:
            return True

        return self.user_test_func()

    def user_test_func(self):
        raise NotImplementedError(
            "Subclasses of SuperuserBypassMixin must implement user_test_func()"
        )


class FullyActivatedUserMixin(SuperuserBypassMixin):
    """
    Enforces that the user is fully activated (email verified, MFA enabled,
    profile complete), but allows superusers to bypass.
    If check fails, redirects to profile edit with a warning.
    """

    redirect_url = reverse_lazy("account_edit")
    login_redirect_url = reverse_lazy("account_auth")

    def user_test_func(self):
        user = self.request.user

        # Block guests
        if not user.is_authenticated:
            return False

        # Check regular user activation state
        return user.is_fully_activated

    def handle_no_permission(self):
        user = self.request.user
        if not user.is_authenticated:
            messages.warning(self.request, "Please sign in to access this feature.")
            return redirect(self.login_redirect_url)

        messages.warning(
            self.request,
            getattr(
                self.request,
                "permission_denied_message",
                "Please complete your profile to access this feature.",
            ),
        )
        return redirect(
            getattr(self, "permission_denied_redirect_url", self.redirect_url)
        )
