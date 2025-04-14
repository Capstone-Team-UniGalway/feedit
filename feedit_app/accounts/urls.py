from django.urls import path
from .views import AuthView, LogoutView

urlpatterns = [
    path("auth", AuthView.as_view(), name="account_auth"),
    path("logout", LogoutView.as_view(), name="account_logout"),
]
