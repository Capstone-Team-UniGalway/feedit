from django.urls import path
from .views import (
    AuthView,
    LogoutView,
    EmailConfirmView,
    ConfirmSuccessView,
    EmailVerificationSentView,
)

urlpatterns = [
    path("auth", AuthView.as_view(), name="account_auth"),
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
]
