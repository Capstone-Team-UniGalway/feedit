from allauth.account.auth_backends import AuthenticationBackend as AllauthBackend
from django.contrib.auth import get_user_model

UserModel = get_user_model()


class SoftDeleteAwareBackend(AllauthBackend):

    def authenticate(self, request, **credentials):
        print(f"SoftDeleteAwareBackend.authenticate called with credentials: {credentials}")

        # Map 'login' to 'username' if present
        if 'login' in credentials and 'username' not in credentials:
            credentials['username'] = credentials['login']

        # Try to get the user directly first for debugging
        if 'username' in credentials and 'password' in credentials:
            try:
                email = credentials['username']
                user_direct = UserModel.objects.get(email=email)
                print(f"Found user directly: {user_direct.email}, Active: {user_direct.is_active}")
            except UserModel.DoesNotExist:
                print(f"User with email {credentials.get('username')} not found directly")

        # Call the parent authenticate method
        user = super().authenticate(request, **credentials)
        print(f"Parent authenticate returned: {user}")

        # If no user, or soft-deleted — deny login
        if user is None:
            print("Authentication failed: user is None")
            return None

        if getattr(user, "is_deleted", False):
            print(f"Authentication failed: user {user.email} is deleted")
            return None

        print(f"Authentication successful for user: {user.email}")
        return user
