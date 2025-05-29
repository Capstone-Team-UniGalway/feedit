from django.urls import path

from .views import (
    CompanyDetailView,
    CompanyEmployeeDirectoryView,
    CreateCompanyView,
    DeleteCompanyView,
    EditCompanyView,
    LeaveCompanyView,
    PublicCompanyListView,
)

app_name = "companies"

urlpatterns = [
    path("", PublicCompanyListView.as_view(), name="list"),  # /companies/
    path("<int:pk>/", CompanyDetailView.as_view(), name="detail"),  # /companies/5/
    path("create/", CreateCompanyView.as_view(), name="create"),  # /companies/create/
    path(
        "<int:pk>/edit/", EditCompanyView.as_view(), name="edit"
    ),  # /companies/5/edit/
    path(
        "<int:pk>/delete/", DeleteCompanyView.as_view(), name="delete"
    ),  # /companies/5/delete/
    path("leave/", LeaveCompanyView.as_view(), name="leave"),  # /companies/leave/
    path(
        "directory/", CompanyEmployeeDirectoryView.as_view(), name="directory"
    ),  # /companies/directory/
    path(
        "<int:pk>/directory/",
        CompanyEmployeeDirectoryView.as_view(),
        name="company_directory",
    ),  # /companies/123/directory/
]
