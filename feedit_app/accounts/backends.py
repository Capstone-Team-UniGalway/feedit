from allauth.account.auth_backends import AuthenticationBackend as AllauthBackend
from django.contrib.auth import get_user_model

UserModel = get_user_model()


class SoftDeleteAwareBackend(AllauthBackend):

    def authenticate(self, request, **credentials):
        user = super().authenticate(request, **credentials)

        # If no user, or soft-deleted — deny login
        if user is None or getattr(user, "is_deleted", False):
            return None

        return user
