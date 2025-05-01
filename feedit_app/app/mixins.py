from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse_lazy


class SuperuserBypassMixin(UserPassesTestMixin):
    """
    A reusable mixin that allows superusers to bypass the `test_func` check.
    Subclasses must implement `user_test_func()`.
    """

    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        if self.request.user.is_superuser:
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

    def user_test_func(self):
        # Ensure only authenticated users are checked here
        user = self.request.user
        return user.is_fully_activated

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            # Let LoginRequiredMixin handle the redirect
            return super().handle_no_permission()
        messages.warning(
            self.request,
            "Please complete your profile to access this feature.",
        )
        return redirect(self.redirect_url)
