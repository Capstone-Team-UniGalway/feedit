from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Prefetch
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.contrib import messages
from django.utils import timezone
from .models import Company, CompanyJoinRequest, CompanyClaimRequest
from reviews.models import ReviewReply
from app.mixins import SuperuserBypassMixin
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add user's pending join requests to context
        if self.request.user.is_authenticated:
            pending_requests = CompanyJoinRequest.objects.filter(
                user=self.request.user,
                status=CompanyJoinRequest.RequestStatus.PENDING
            ).values_list('company_id', flat=True)
            context['pending_requests'] = list(pending_requests)
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
        reviews = (
            self.object.reviews.filter(is_deleted=False)
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
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context["page_obj"] = page_obj
        context["reviews"] = page_obj.object_list
        context["is_paginated"] = page_obj.has_other_pages()

        # Add user's pending join requests to context
        if self.request.user.is_authenticated:
            pending_requests = CompanyJoinRequest.objects.filter(
                user=self.request.user,
                status=CompanyJoinRequest.RequestStatus.PENDING
            ).values_list('company_id', flat=True)
            context['pending_requests'] = list(pending_requests)

            # Add user's pending claim requests to context
            pending_claim_requests = CompanyClaimRequest.objects.filter(
                user=self.request.user,
                status=CompanyClaimRequest.RequestStatus.PENDING
            ).values_list('company_id', flat=True)
            context['pending_claim_requests'] = list(pending_claim_requests)

        return context


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

    def get_initial(self):
        """Pre-fill form with data from URL parameters"""
        initial = super().get_initial()
        name = self.request.GET.get('name')
        if name:
            initial['name'] = name
        return initial

    def form_valid(self, form):
        """Associate the company with the current user"""
        company = form.save(commit=False)

        # Set the employer to the current user if they are an employer
        if self.request.user.type == "employer":
            company.employer = self.request.user

        company.save()

        # Set the user's workplace to this company
        self.request.user.workplace = company
        self.request.user.save()

        messages.success(self.request, f"You have successfully created {company.name}!")
        return super().form_valid(form)


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


class JoinCompanyListView(LoginRequiredMixin, ListView):
    """View for listing companies that a user can join"""
    model = Company
    template_name = "pages/join_company.html"
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
        # Add user's pending join requests to context
        if self.request.user.is_authenticated:
            pending_requests = CompanyJoinRequest.objects.filter(
                user=self.request.user,
                status=CompanyJoinRequest.RequestStatus.PENDING
            ).values_list('company_id', flat=True)
            context['pending_requests'] = list(pending_requests)
        return context


class JoinCompanyRequestView(LoginRequiredMixin, View):
    """View for handling company join requests"""

    def post(self, request, *args, **kwargs):
        company = get_object_or_404(Company, pk=kwargs.get('pk'), is_deleted=False)

        # Check if user already has a workplace
        if request.user.workplace:
            messages.error(request, "You are already associated with a company.")
            return redirect('companies:detail', pk=company.pk)

        # Check if user already has a pending request for this company
        existing_request = CompanyJoinRequest.objects.filter(
            user=request.user,
            company=company,
            status=CompanyJoinRequest.RequestStatus.PENDING
        ).first()

        if existing_request:
            messages.info(request, "You already have a pending request to join this company.")
        else:
            # Create a new join request
            join_request = CompanyJoinRequest.objects.create(
                user=request.user,
                company=company,
                message=request.POST.get('message', '')
            )
            messages.success(
                request,
                f"Your request to join {company.name} has been submitted and is pending approval."
            )

        return redirect('companies:detail', pk=company.pk)


class ManageJoinRequestsView(LoginRequiredMixin, SuperuserBypassMixin, ListView):
    """View for company admins to manage join requests"""
    model = CompanyJoinRequest
    template_name = "pages/companies/manage_requests.html"
    context_object_name = "requests"
    paginate_by = 10

    def user_test_func(self):
        # Only company employers can manage join requests
        return self.request.user.type == "employer" and hasattr(self.request.user, "company")

    def get_queryset(self):
        return CompanyJoinRequest.objects.filter(
            company=self.request.user.company,
            status=CompanyJoinRequest.RequestStatus.PENDING
        ).select_related('user').order_by('-created_at')


class ProcessJoinRequestView(LoginRequiredMixin, SuperuserBypassMixin, View):
    """View for approving or rejecting join requests"""

    def user_test_func(self):
        # Only company employers can process join requests
        return self.request.user.type == "employer" and hasattr(self.request.user, "company")

    def post(self, request, *args, **kwargs):
        join_request = get_object_or_404(
            CompanyJoinRequest,
            pk=kwargs.get('pk'),
            company=request.user.company,
            status=CompanyJoinRequest.RequestStatus.PENDING
        )

        action = request.POST.get('action')

        if action == 'approve':
            join_request.approve(processed_by=request.user)
            messages.success(
                request,
                f"{join_request.user.get_full_name()} has been added to your company."
            )
        elif action == 'reject':
            join_request.reject(processed_by=request.user)
            messages.info(
                request,
                f"You have rejected {join_request.user.get_full_name()}'s request to join your company."
            )

        return redirect('companies:manage_requests')


class LeaveCompanyView(LoginRequiredMixin, View):
    """View for users to leave their current company"""

    def post(self, request, *args, **kwargs):
        # Check if user has a workplace
        if not request.user.workplace:
            messages.error(request, "You are not currently associated with any company.")
            return redirect('dashboard')

        company_name = request.user.workplace.name

        # Remove the workplace association
        request.user.workplace = None
        request.user.save()

        messages.success(request, f"You have successfully left {company_name}.")
        return redirect('dashboard')


class CompanyClaimRequestView(LoginRequiredMixin, View):
    """View for handling company claim requests"""

    def post(self, request, *args, **kwargs):
        company = get_object_or_404(Company, pk=kwargs.get('pk'), is_deleted=False)

        # Check if user already has a workplace
        if request.user.workplace:
            messages.error(request, "You are already associated with a company.")
            return redirect('companies:detail', pk=company.pk)

        # Check if company is already claimed
        if company.employer and company.employer != request.user:
            messages.error(request, "This company is already claimed by another user.")
            return redirect('companies:detail', pk=company.pk)

        # Check if user already has a pending claim request for this company
        existing_request = CompanyClaimRequest.objects.filter(
            user=request.user,
            company=company,
            status=CompanyClaimRequest.RequestStatus.PENDING
        ).first()

        if existing_request:
            messages.info(request, "You already have a pending claim request for this company.")
            return redirect('companies:detail', pk=company.pk)

        # Handle file upload
        verification_document = request.FILES.get('verification_document')

        # Create a new claim request
        claim_request = CompanyClaimRequest.objects.create(
            user=request.user,
            company=company,
            message=request.POST.get('message', ''),
            verification_document=verification_document
        )

        messages.success(
            request,
            f"Your request to claim {company.name} has been submitted and is pending approval."
        )

        return redirect('companies:detail', pk=company.pk)


class CompanyDisputeClaimView(LoginRequiredMixin, View):
    """View for handling company claim disputes"""

    def post(self, request, *args, **kwargs):
        company = get_object_or_404(Company, pk=kwargs.get('pk'), is_deleted=False)

        # Check if company is not claimed
        if not company.employer:
            messages.error(request, "This company is not claimed by anyone yet. You can claim it directly.")
            return redirect('companies:detail', pk=company.pk)

        # Check if user is trying to dispute their own claim
        if company.employer == request.user:
            messages.error(request, "You are already the owner of this company.")
            return redirect('companies:detail', pk=company.pk)

        # Check if user already has a pending dispute for this company
        existing_request = CompanyClaimRequest.objects.filter(
            user=request.user,
            company=company,
            status=CompanyClaimRequest.RequestStatus.PENDING
        ).first()

        if existing_request:
            messages.info(request, "You already have a pending dispute for this company.")
            return redirect('companies:detail', pk=company.pk)

        # Handle file upload (required for disputes)
        verification_document = request.FILES.get('verification_document')
        if not verification_document:
            messages.error(request, "Verification document is required for ownership disputes.")
            return redirect('companies:detail', pk=company.pk)

        # Create a new claim request (disputes are just claim requests with a different context)
        claim_request = CompanyClaimRequest.objects.create(
            user=request.user,
            company=company,
            message=request.POST.get('message', ''),
            verification_document=verification_document
        )

        messages.success(
            request,
            f"Your ownership dispute for {company.name} has been submitted and is pending review."
        )

        return redirect('companies:detail', pk=company.pk)


class ManageClaimRequestsView(LoginRequiredMixin, SuperuserBypassMixin, ListView):
    """View for admins to manage company claim requests"""
    model = CompanyClaimRequest
    template_name = "pages/companies/manage_claims.html"
    context_object_name = "requests"
    paginate_by = 10

    def user_test_func(self):
        # Only superusers can manage claim requests
        return self.request.user.is_superuser

    def get_queryset(self):
        return CompanyClaimRequest.objects.filter(
            status=CompanyClaimRequest.RequestStatus.PENDING
        ).select_related('user', 'company').order_by('-created_at')


class ProcessClaimRequestView(LoginRequiredMixin, SuperuserBypassMixin, View):
    """View for approving or rejecting claim requests"""

    def user_test_func(self):
        # Only superusers can process claim requests
        return self.request.user.is_superuser

    def post(self, request, *args, **kwargs):
        claim_request = get_object_or_404(
            CompanyClaimRequest,
            pk=kwargs.get('pk'),
            status=CompanyClaimRequest.RequestStatus.PENDING
        )

        action = request.POST.get('action')

        if action == 'approve':
            claim_request.approve(processed_by=request.user)
            messages.success(
                request,
                f"{claim_request.user.get_full_name()} is now the owner of {claim_request.company.name}."
            )
        elif action == 'reject':
            claim_request.reject(processed_by=request.user)
            messages.info(
                request,
                f"You have rejected {claim_request.user.get_full_name()}'s claim to {claim_request.company.name}."
            )

        return redirect('companies:manage_claims')
