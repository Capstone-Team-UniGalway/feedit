from django.urls import path
from . import views

urlpatterns = [
    path("", views.ThreadListView.as_view(), name="thread_list"),
    path("<int:pk>/", views.ThreadDetailView.as_view(), name="thread_detail"),
    path("create/", views.ThreadCreateView.as_view(), name="thread_create"),
    path("<int:pk>/reply/", views.ThreadReplyCreateView.as_view(), name="thread_reply"),
    path("<int:pk>/edit/", views.ThreadUpdateView.as_view(), name="thread_update"),
    path("<int:pk>/delete/", views.ThreadDeleteView.as_view(), name="thread_delete"),
]
