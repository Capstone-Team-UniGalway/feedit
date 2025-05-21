from django.urls import path
from . import views

app_name = "requests"

urlpatterns = [
    path("", views.RequestListView.as_view(), name="list"),
    path("create/", views.CreateRequestView.as_view(), name="create"),
    path(
        "create/<int:company_id>/",
        views.CreateRequestView.as_view(),
        name="create_with_id",
    ),
    path("<int:pk>/", views.RequestDetailView.as_view(), name="detail"),
    path("<int:pk>/process/", views.ProcessRequestView.as_view(), name="process"),
    path("<int:pk>/cancel/", views.CancelRequestView.as_view(), name="cancel"),
    path(
        "<int:request_id>/reply/", views.CreateRequestReplyView.as_view(), name="reply"
    ),
    path(
        "company/<int:company_id>/",
        views.RequestListView.as_view(),
        name="company",
    ),
]
