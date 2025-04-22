from django.urls import path, include
from allauth.mfa import urls as allauth_mfa_urls
from allauth.account.views import ReauthenticateView
from allauth.mfa.base.views import AuthenticateView
from .views import (
    AuthView,
    AuthRedirectView,
    LogoutView,
    EmailConfirmView,
    ConfirmSuccessView,
    EmailVerificationSentView,
    ResendEmailVerificationView,
    BypassEmailVerificationView,
    ProfileView,
    EditProfileView,
    CloseAccountView,
    AuthPasswordResetDonePartial,
    CustomPasswordResetFromKeyView,
    CustomPasswordResetView,
    DashboardView,
    UserSearchView,
    DirectLoginView,
)

urlpatterns = [
    path("", ProfileView.as_view(), name="account_profile"),
    path("edit", EditProfileView.as_view(), name="account_edit"),
    path("auth", AuthView.as_view(), name="account_auth"),  # canonical
    path(
        "login", AuthRedirectView.as_view(), name="account_login"
    ),  # required by Allauth
    path(
        "signup", AuthRedirectView.as_view(), name="account_signup"
    ),  # required by Allauth
    path("logout", LogoutView.as_view(), name="account_logout"),
    path(
        "confirm-email/<str:key>/",
        EmailConfirmView.as_view(),
        name="account_confirm_email",
    ),
    path(
        "confirm-email/success/",
        ConfirmSuccessView.as_view(),
        name="account_confirm_success",
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
    path(
        "bypass-verification/",
        BypassEmailVerificationView.as_view(),
        name="account_bypass_verification",
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
    path("mfa/", include(allauth_mfa_urls)),
    path(
        "reauthenticate/",
        ReauthenticateView.as_view(),
        name="account_reauthenticate",
    ),
    path("mfa/authenticate/", AuthenticateView.as_view(), name="mfa_authenticate"),
    path("dashboard", DashboardView.as_view(), name="dashboard"),
    path("api/search-users/", UserSearchView.as_view(), name="api_search_users"),
    path("direct-login/", DirectLoginView.as_view(), name="direct_login"),
]
