from django.contrib.auth.mixins import UserPassesTestMixin


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
