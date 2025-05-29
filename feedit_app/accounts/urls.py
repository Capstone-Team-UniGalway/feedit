from allauth.account.views import ReauthenticateView
from allauth.mfa import urls as allauth_mfa_urls
from django.urls import include, path

from .views import (
    AuthPasswordResetDonePartial,
    AuthRedirectView,
    AuthView,
    CloseAccountView,
    ConfirmSuccessView,
    CustomAuthenticateView,
    CustomPasswordResetFromKeyView,
    CustomPasswordResetView,
    EditProfileView,
    EmailConfirmView,
    EmailVerificationSentView,
    LogoutView,
    ProfileView,
    ResendEmailVerificationView,
    UserSearchView,
    MentionsListView,
)

urlpatterns = [
    path("", ProfileView.as_view(), name="account_profile"),
    path("edit/", EditProfileView.as_view(), name="account_edit"),
    path("mentions/", MentionsListView.as_view(), name="account_mentions"),
    path("auth/", AuthView.as_view(), name="account_auth"),  # canonical
    path(
        "login/", AuthRedirectView.as_view(), name="account_login"
    ),  # required by Allauth
    path(
        "signup/", AuthRedirectView.as_view(), name="account_signup"
    ),  # required by Allauth
    path("logout/", LogoutView.as_view(), name="account_logout"),
    path(
        "confirm-email/success/",
        ConfirmSuccessView.as_view(),
        name="account_confirm_success",
    ),
    path(
        "confirm-email/<str:key>/",
        EmailConfirmView.as_view(),
        name="account_confirm_email",
    ),
    path(
        "email-verification-sent/",
        EmailVerificationSentView.as_view(),
        name="account_email_verification_sent",
    ),
    path(
        "resend-verification/",
        ResendEmailVerificationView.as_view(),
        name="account_email_verification_send",
    ),
    path("close", CloseAccountView.as_view(), name="account_close"),
    path(
        "password/reset/",
        CustomPasswordResetView.as_view(),
        name="account_reset_password",
    ),
    path(
        "password/reset/done/",
        AuthPasswordResetDonePartial.as_view(),
        name="account_reset_password_done",
    ),
    # UIDB64 + token – actual valid route
    path(
        "password/reset/key/<uidb64>/<token>/",
        CustomPasswordResetFromKeyView.as_view(),
        name="account_reset_password_from_key",
    ),
    # UIDB36 + key – dummy fallback just for internal reverse()
    path(
        "password/reset/key/<uidb36>/<key>/",
        CustomPasswordResetFromKeyView.as_view(),
    ),
    path(
        "mfa/authenticate/", CustomAuthenticateView.as_view(), name="mfa_authenticate"
    ),
    path("mfa/", include(allauth_mfa_urls)),
    path(
        "reauthenticate/",
        ReauthenticateView.as_view(),
        name="account_reauthenticate",
    ),
    path("api/search-users/", UserSearchView.as_view(), name="api_search_users"),
    path("mentions/", MentionsListView.as_view(), name="account_mentions"),
    # This must be the last path as it takes everything after /account/ as identifier
    path("<str:identifier>/", ProfileView.as_view(), name="account_public_profile"),
]
