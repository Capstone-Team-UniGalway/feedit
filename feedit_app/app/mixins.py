from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.core.exceptions import PermissionDenied


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
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_fully_activated:
            raise PermissionDenied("Your account is not fully activated.")
        return super().dispatch(request, *args, **kwargs)
