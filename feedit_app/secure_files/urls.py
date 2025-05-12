from django.urls import path
from . import views

app_name = 'secure_files'

urlpatterns = [
    # General secure file routes
    path('upload/<int:content_type_id>/<int:object_id>/',
         views.SecureFileUploadView.as_view(),
         name='upload'),
    path('delete/<int:file_id>/',
         views.SecureFileDeleteView.as_view(),
         name='delete'),
    path('download/<int:file_id>/',
         views.SecureFileDownloadView.as_view(),
         name='download'),

    # Specialized routes for request files with permission checks
    path('requests/join/<int:join_request_id>/files/<int:secure_file_id>/download/',
         views.JoinRequestFileDownloadView.as_view(),
         name='download_join_request_file'),
    path('requests/claim/<int:claim_request_id>/files/<int:secure_file_id>/download/',
         views.ClaimRequestFileDownloadView.as_view(),
         name='download_claim_request_file'),
]
