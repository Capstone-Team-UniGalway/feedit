from django.db.models import Q, Prefetch
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.contrib import messages
from .models import Company
from reviews.models import ReviewReply
from app.mixins import FullyActivatedUserMixin
from .forms import CompanyForm
from django.core.paginator import Paginator


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
        else:
            context["has_reviewed"] = False

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
    """Route: /company/<int:pk>/edit | GET/PUT"""

    http_method_names = ["get", "put"]

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
    """View for users to leave their current company"""

    def post(self, request, *args, **kwargs):
        # Check if user has a workplace
        if not request.user.workplace:
            messages.error(
                request, "You are not currently associated with any company."
            )
            return redirect("dashboard")

        company_name = request.user.workplace.name

        # Remove the workplace association
        request.user.workplace = None
        request.user.save()

        messages.success(request, f"You have successfully left {company_name}.")
        return redirect("dashboard")
