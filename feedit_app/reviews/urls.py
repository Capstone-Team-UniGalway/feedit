from django.urls import path
from . import views

app_name = "reviews"

urlpatterns = [
    path("company/<int:company_id>/create/", views.create_review, name="create_review"),
    path(
        "<int:review_id>/reply/", views.create_review_reply, name="create_review_reply"
    ),
]
