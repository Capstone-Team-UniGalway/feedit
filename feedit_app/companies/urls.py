from django.urls import path
from .views import (
    PublicCompanyListView,
    CompanyDetailView,
    CreateCompanyView,
    EditCompanyView,
    DeleteCompanyView,
    JoinCompanyListView,
    JoinCompanyRequestView,
    ManageJoinRequestsView,
    ProcessJoinRequestView,
    LeaveCompanyView,
    CompanyClaimRequestView,
    CompanyDisputeClaimView,
    ManageClaimRequestsView,
    ProcessClaimRequestView,
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
    path(
        "join/", JoinCompanyListView.as_view(), name="join"
    ),  # /companies/join/
    path(
        "<int:pk>/join-request/", JoinCompanyRequestView.as_view(), name="join_request"
    ),  # /companies/5/join-request/
    path(
        "manage-requests/", ManageJoinRequestsView.as_view(), name="manage_requests"
    ),  # /companies/manage-requests/
    path(
        "process-request/<int:pk>/", ProcessJoinRequestView.as_view(), name="process_request"
    ),  # /companies/process-request/5/
    path(
        "leave/", LeaveCompanyView.as_view(), name="leave"
    ),  # /companies/leave/
    path(
        "<int:pk>/claim/", CompanyClaimRequestView.as_view(), name="claim_request"
    ),  # /companies/5/claim/
    path(
        "<int:pk>/dispute/", CompanyDisputeClaimView.as_view(), name="dispute_claim"
    ),  # /companies/5/dispute/
    path(
        "manage-claims/", ManageClaimRequestsView.as_view(), name="manage_claims"
    ),  # /companies/manage-claims/
    path(
        "process-claim/<int:pk>/", ProcessClaimRequestView.as_view(), name="process_claim"
    ),  # /companies/process-claim/5/
]
