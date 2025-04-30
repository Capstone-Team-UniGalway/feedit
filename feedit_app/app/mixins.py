from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse_lazy


class SuperuserBypassMixin(UserPassesTestMixin):
    """
    A reusable mixin that allows superusers to bypass the `test_func` check.
    Subclasses must implement `user_test_func()`.
    """

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        return self.user_test_func()

    def user_test_func(self):
        raise NotImplementedError(
            "Subclasses of SuperuserBypassMixin must implement user_test_func()"
        )


class FullyActivatedUserMixin(LoginRequiredMixin):
    """
    Enforces that the user is fully activated (email verified, MFA enabled,
    profile complete). If not, redirect to profile edit with a warning.
    """

    redirect_url = reverse_lazy("account_edit")

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_fully_activated:
            messages.warning(
                request,
                "Please complete your profile, to access this feature.",
            )
            return redirect(self.redirect_url)
        return super().dispatch(request, *args, **kwargs)
