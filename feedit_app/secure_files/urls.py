from django.urls import path

from . import views

app_name = "secure_files"

urlpatterns = [
    # General secure file routes
    path(
        "new/<int:content_type_id>/<int:object_id>/",
        views.SecureFileUploadView.as_view(),
        name="new",
    ),
    path("<int:file_id>/delete/", views.SecureFileDeleteView.as_view(), name="delete"),
    path(
        "<int:file_id>/",
        views.SecureFileDownloadView.as_view(),
        name="download",
    ),
]
