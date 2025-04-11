from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from .models import Company
from app.mixins import SuperuserBypassMixin
from .forms import CompanyForm


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


class CreateCompanyView(LoginRequiredMixin, SuperuserBypassMixin, CreateView):
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


class EditCompanyView(LoginRequiredMixin, SuperuserBypassMixin, UpdateView):
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


class DeleteCompanyView(LoginRequiredMixin, SuperuserBypassMixin, View):
    http_method_names = ["post"]

    def user_test_func(self):
        company = get_object_or_404(Company, pk=self.kwargs["pk"], is_deleted=False)
        return self.request.user == company.employer

    def post(self, request, *args, **kwargs):
        success_url = reverse_lazy("dashboard")
        company = get_object_or_404(Company, pk=self.kwargs["pk"], is_deleted=False)
        company.delete()  # Uses soft-delete from BaseModel
        return redirect(success_url)
