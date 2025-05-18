from django.urls import path
from .views import (
    PublicCompanyListView,
    CompanyDetailView,
    CreateCompanyView,
    EditCompanyView,
    DeleteCompanyView,
    LeaveCompanyView,
    ManageRequestsView,
    ManageClaimsView,
    ProcessClaimView,
    CompanyEmployeeDirectoryView,
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
        "<int:pk>/manage-requests/", ManageRequestsView.as_view(), name="manage_requests"
    ),  # /companies/5/manage-requests/
    path(
        "manage-claims/", ManageClaimsView.as_view(), name="manage_claims"
    ),  # /companies/manage-claims/
    path(
        "process-claim/<int:pk>/", ProcessClaimView.as_view(), name="process_claim"
    ),  # /companies/process-claim/5/
    path(
        "directory/", CompanyEmployeeDirectoryView.as_view(), name="directory"
    ),  # /companies/directory/
]
