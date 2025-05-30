from accounts.models import User
from app.mixins import FullyActivatedUserMixin
from company_requests.models import Request
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.paginator import Paginator
from django.db.models import Prefetch, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView, View
from reviews.models import ReviewReply

from .forms import CompanyForm
from .models import Company


class PublicCompanyListView(ListView):
    """Route: /companies | Permission: all"""

    http_method_names = ["get"]

    model = Company
    template_name = "pages/companies/company_list.html"
    context_object_name = "companies"
    paginate_by = 8

    def get_queryset(self):
        query = self.request.GET.get("q", "")
        qs = Company.objects.filter(is_deleted=False)
        if query:
            qs = qs.filter(Q(name__icontains=query) | Q(industry__icontains=query))
        return qs.order_by("name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Add pending requests context for authenticated users
        if user.is_authenticated and not user.workplace:
            # Get IDs of companies where the user has pending join requests
            pending_requests = Request.objects.filter(
                author=user,
                type="join",  # Using string value instead of enum
                status="pending",  # Using string value instead of enum
            ).values_list("company_id", flat=True)

            context["pending_requests"] = list(pending_requests)
        else:
            context["pending_requests"] = []

        return context


class CompanyDetailView(DetailView):
    """Route: /companies/<int:pk> | Permission: all"""

    http_method_names = ["get"]
    model = Company
    template_name = "pages/companies/company_profile.html"
    context_object_name = "company"

    def get_object(self, queryset=None):
        company = super().get_object(queryset)
        if company.is_deleted:
            raise Http404("Company not found")
        return company

    def get_context_data(self, **kwargs):
        """
        select_related("user") - Django fetches all the reviews and their associated
        users in one query using SQL joins. Without it, for each review, Django will hit
        the database to fetch the related user causing N+1 query problem
        .prefetch_related("replies") - fetches replies within same query to avoid N+1
        """
        context = super().get_context_data(**kwargs)
        company = self.object
        request = self.request
        user = request.user

        # --- Paginated reviews with replies ---
        reviews = (
            company.reviews.filter(is_deleted=False)
            .select_related("user")
            .prefetch_related(
                Prefetch(
                    "replies",
                    queryset=ReviewReply.objects.filter(is_deleted=False).order_by(
                        "-created_at"
                    ),
                )
            )
            .order_by("-created_at")
        )
        paginator = Paginator(reviews, 5)  # 5 reviews per page
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context["page_obj"] = page_obj
        context["reviews"] = page_obj.object_list
        context["is_paginated"] = page_obj.has_other_pages()

        # --- User-specific context ---
        context["is_employer"] = user.is_authenticated and user == company.employer
        context["is_employee"] = user.is_authenticated and user.workplace == company

        # User has reviewed (exclude deleted reviews)
        if user.is_authenticated:
            context["has_reviewed"] = company.reviews.filter(
                user=user, is_deleted=False
            ).exists()

            # Add pending requests context for authenticated users without a workplace
            if not user.workplace:
                # Check if user has a pending join request for this company
                has_pending_request = Request.objects.filter(
                    author=user,
                    company=company,
                    type="join",  # Using string value instead of enum
                    status="pending",  # Using string value instead of enum
                ).exists()

                context["pending_requests"] = (
                    [company.id] if has_pending_request else []
                )
            else:
                context["pending_requests"] = []
        else:
            context["has_reviewed"] = False
            context["pending_requests"] = []

        return context


class CreateCompanyView(FullyActivatedUserMixin, CreateView):
    """Route: /companies/create | GET/POST | Permission: employer with no company"""

    http_method_names = ["get", "post"]

    model = Company
    form_class = CompanyForm
    template_name = "pages/companies/company_form.html"
    success_url = reverse_lazy("dashboard")

    def user_test_func(self):
        user = self.request.user

        is_employer_without_company = user.type == "employer" and not hasattr(
            user, "company"
        )
        is_employee_without_company = user.type == "employee" and user.workplace is None
        return is_employer_without_company or is_employee_without_company

    def handle_no_permission(self):
        return redirect(self.success_url)  # Add message in middleware or template

    def get_initial(self):
        """Pre-fill form with data from URL parameters"""
        initial = super().get_initial()
        name = self.request.GET.get("name")
        if name:
            initial["name"] = name
        return initial

    def form_valid(self, form):
        """Associate the company with the current user"""
        company = form.save(commit=False)

        # Set the employer to the current user if they are an employer
        if self.request.user.type == "employer":
            company.employer = self.request.user

        company.save()

        # Set the user's workplace to this company if user is employee
        if self.request.user.type == "employee":
            self.request.user.workplace = company
            self.request.user.save()

        messages.success(self.request, f"You have successfully created {company.name}!")
        return super().form_valid(form)


class EditCompanyView(FullyActivatedUserMixin, UpdateView):
    """Route: /company/<int:pk>/edit | GET/POST"""

    http_method_names = ["get", "post"]

    model = Company
    form_class = CompanyForm
    template_name = "pages/companies/company_form.html"
    success_url = reverse_lazy("dashboard")

    def user_test_func(self):
        company = self.get_object()
        user = self.request.user

        return user.type == "employer" and user == company.employer

    def handle_no_permission(self):
        return redirect(self.success_url)

    def get_queryset(self):
        return Company.objects.filter(is_deleted=False)


class DeleteCompanyView(FullyActivatedUserMixin, View):
    http_method_names = ["post"]

    def user_test_func(self):
        company = get_object_or_404(Company, pk=self.kwargs["pk"], is_deleted=False)
        return self.request.user == company.employer

    def post(self, request, *args, **kwargs):
        success_url = reverse_lazy("dashboard")
        company = get_object_or_404(Company, pk=self.kwargs["pk"], is_deleted=False)
        company.delete()  # Uses soft-delete from BaseModel
        return redirect(success_url)


class LeaveCompanyView(FullyActivatedUserMixin, View):
    """Allows both employees and employers to leave their current company"""

    def user_test_func(self):
        self.permission_denied_message = (
            "You are not currently associated with any company."
        )
        self.permission_denied_redirect_url = "dashboard"
        user = self.request.user

        return user.workplace or hasattr(user, "company")

    def post(self, request, *args, **kwargs):
        user = request.user

        # Case 1: Employee leaving workplace
        if user.type == "employee" and user.workplace:
            name = user.workplace.name
            user.workplace = None
            user.save()
            messages.success(request, f"You have successfully left {name}.")

        # Case 2: Employer relinquishing their owned company
        elif user.type == "employer" and hasattr(user, "company") and user.company:
            company = user.company
            company_name = company.name
            company.employer = None
            company.save()
            # Optional: user.is_approved = False  # if you want to reset approval
            messages.success(
                request, f"You have successfully unlinked from {company_name}."
            )

        return redirect("dashboard")


class CompanyEmployeeDirectoryView(UserPassesTestMixin, ListView):
    """
    Directory of employees for a company.
    - Route: /companies/<company_id>/directory/ or /companies/directory/
    - Guests can only view with company_id in path.
    - Authenticated users can view their own company without company_id.
    """

    http_method_names = ["get"]
    template_name = "pages/companies/employee_directory.html"
    context_object_name = "employees"
    paginate_by = 12

    # ========== PERMISSION GATE ==========

    def test_func(self):
        self.company = None  # Will be attached dynamically

        company_id = self.kwargs.get("pk")

        if company_id:
            self.company = get_object_or_404(Company, pk=company_id)
            return True  # Any user or guest can view if company exists

        user = self.request.user
        if not user.is_authenticated:
            return False  # No access to own company directory if not logged in

        # Figure out user's own company
        self.company = getattr(user, "workplace", None) or getattr(
            user, "company", None
        )
        return bool(self.company)

    def handle_no_permission(self):
        user = self.request.user
        company_id = self.kwargs.get("pk")

        if not user.is_authenticated and not company_id:
            messages.warning(self.request, "Sign in to view your company directory.")
            return redirect("account_auth")

        if user.is_authenticated and not company_id:
            messages.warning(self.request, "Join a company to view the directory.")
            return redirect("companies:list")  # Replace with actual path name

        return super().handle_no_permission()

    # ========== QUERYSET BUILDER ==========

    def get_queryset(self):
        user = self.request.user
        company = self.company

        base_query = User.objects.filter(is_active=True, is_deleted=False).filter(
            Q(workplace=company) | Q(company=company)
        )

        # Admins in company: see all
        if user.is_authenticated and user.is_superuser:
            return base_query.order_by("first_name", "last_name")

        # Guests: only public users
        if not user.is_authenticated:
            return base_query.filter(privacy=User.PrivacyType.PUBLIC)

        is_own_company = (
            getattr(user, "company", None) == company
            or getattr(user, "workplace", None) == company
        )

        if is_own_company:
            if user.type == User.UserType.EMPLOYER:
                return base_query  # See all users including self
            elif user.type == User.UserType.EMPLOYEE:
                return base_query.filter(
                    Q(privacy=User.PrivacyType.PUBLIC)
                    | Q(privacy=User.PrivacyType.INTERNAL)
                )
        else:
            return base_query.filter(privacy=User.PrivacyType.PUBLIC)

    # ========== CONTEXT ==========

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        company = self.company

        context["company"] = company
        context["search_query"] = self.request.GET.get("q", "")

        # Show employer if privacy allows
        employer = company.employer if company else None
        if employer:
            if employer.privacy == User.PrivacyType.PUBLIC:
                context["employer"] = employer
            elif employer.privacy == User.PrivacyType.INTERNAL:
                if user.is_authenticated and (
                    user.is_superuser
                    or getattr(user, "company", None) == company
                    or getattr(user, "workplace", None) == company
                ):
                    context["employer"] = employer
            elif user == employer:
                context["employer"] = employer

        return context
