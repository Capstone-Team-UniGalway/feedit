from django.urls import path
from .views import CreateReviewView, CreateReviewReplyView, ToggleGuestNameFieldView

app_name = "reviews"

urlpatterns = [
    path("create/<int:company_id>/", CreateReviewView.as_view(), name="create_review"),
    path(
        "reply/<int:review_id>/",
        CreateReviewReplyView.as_view(),
        name="create_review_reply",
    ),
    path(
        "hx/toggle-guest-name/",
        ToggleGuestNameFieldView.as_view(),
        name="hx_toggle_guest_name",
    ),
]
