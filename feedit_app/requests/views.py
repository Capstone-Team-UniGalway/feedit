from django.views.generic import CreateView, ListView, DetailView, View
from django.utils.functional import cached_property
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType
from app.mixins import FullyActivatedUserMixin
from .models import Request, RequestReply
from .forms import RequestForm, RequestReplyForm
from secure_files.models import SecureFile
from companies.models import Company


class CreateRequestView(FullyActivatedUserMixin, CreateView):
    model = Request
    form_class = RequestForm
    template_name = "pages/requests/create_request.html"

    @cached_property
    def company(self):
        company_id = self.kwargs.get("company_id")
        if company_id:
            return get_object_or_404(Company, id=company_id, is_deleted=False)

        user = self.request.user
        return (
            user.workplace
            if user.type == "employee"
            else getattr(user, "company", None)
        )

    def dispatch(self, request, *args, **kwargs):
        self.request_type = self.determine_request_type()

        # 🔐 Block all access if no company is resolvable
        if self.company is None:
            if self.request.user.type == "employer":
                message = "Find and claim your company! Create it if not in the list."
            else:
                message = "You must join a company before making a request."

            messages.warning(request, message)
            return redirect("companies:list")

        return super().dispatch(request, *args, **kwargs)

    def determine_request_type(self):
        if self.request.user.type == "employer":
            return Request.RequestType.CLAIM
        else:
            if "company_id" in self.kwargs:
                return Request.RequestType.JOIN
            return Request.RequestType.OTHER

    def user_test_func(self):
        user = self.request.user

        if not user.is_authenticated or not user.is_fully_activated:
            return False

        # Block if the request is of type OTHER but the user has no linked company
        if self.request_type == Request.RequestType.OTHER and not self.company:
            self.permission_denied_message = (
                "You need to join a company before making requests."
            )
            self.permission_denied_redirect_url = "companies:list"
            return False

        # Block CLAIM requests if the employer already owns a company
        if self.request_type == Request.RequestType.CLAIM and user.has_company:
            self.permission_denied_message = (
                "You already own a company and cannot submit a claim request."
            )
            self.permission_denied_redirect_url = "dashboard"
            return False

        # Block JOIN requests if the user is already part of a company
        if self.request_type == Request.RequestType.JOIN and user.has_company:
            self.permission_denied_message = (
                "You are already part of a company and cannot submit a join request."
            )
            self.permission_denied_redirect_url = "dashboard"
            return False

        # Block if the user has a pending request of this type
        if self.request_type in [Request.RequestType.JOIN, Request.RequestType.CLAIM]:
            existing = Request.objects.filter(
                author=user,
                type=self.request_type,
                status=Request.RequestStatus.PENDING,
                is_deleted=False,
            ).first()

            if existing:
                self.permission_denied_message = (
                    "You already have a pending request. Please wait for a response or "
                    "cancel it before submitting a new one."
                )
                self.permission_denied_redirect_url = "requests:list"
                return False

        return True

    def get_form_kwargs(self):
        """Pass the current user and request type to the form."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["request_type"] = self.request_type
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["company"] = self.company
        return context

    def get_initial(self):
        initial = super().get_initial()
        company_name = self.company.name

        if self.request_type == Request.RequestType.CLAIM:
            initial["title"] = f"Request to claim {company_name}"
        elif self.request_type == Request.RequestType.JOIN:
            initial["title"] = f"Request to join {company_name}"
        else:
            initial["title"] = f"Request to {company_name}"

        initial["type"] = self.request_type
        return initial

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.company = self.company
        form.instance.type = self.request_type

        if self.request_type == Request.RequestType.CLAIM:
            msg = (
                "Your ownership dispute has been submitted and is pending admin review."
                if self.company.employer
                else (
                    "Your claim request has been submitted and is pending "
                    "admin approval."
                )
            )
        elif self.request_type == Request.RequestType.JOIN:
            msg = "Your join request has been submitted successfully."
        else:
            msg = "Your request has been submitted to your company."

        messages.success(self.request, msg)
        response = super().form_valid(form)

        file = self.request.FILES.get("verification_document")
        if file:
            SecureFile.objects.create(
                content_type=ContentType.objects.get_for_model(Request),
                object_id=self.object.id,
                file=file,
                uploaded_by=self.request.user,
            )
            messages.success(
                self.request, "Verification document uploaded successfully."
            )

        return response


class RequestDetailView(FullyActivatedUserMixin, DetailView):
    model = Request
    template_name = "pages/requests/request_detail.html"
    context_object_name = "request"

    def user_test_func(self):
        user = self.request.user
        obj = self.get_object()

        if not user.is_authenticated or not user.is_fully_activated:
            return False

        if obj.author == user or obj.company.employer == user or user.is_superuser:
            return True

        # Store custom denial reason
        self.permission_denied_message = (
            "You do not have permission to view this request."
        )
        self.permission_denied_redirect_url = "dashboard"
        return False

    def get_queryset(self):
        return Request.objects.filter(is_deleted=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request_obj = self.object
        user = self.request.user

        # Get attached files
        content_type = ContentType.objects.get_for_model(Request)
        files = SecureFile.objects.filter(
            content_type=content_type, object_id=request_obj.id, is_deleted=False
        )

        can_process = request_obj.can_be_processed_by(user)

        context["can_process_request"] = can_process
        context["can_reply"] = can_process or user == request_obj.author
        context["reply_form"] = RequestReplyForm()
        context["files"] = files

        return context


class RequestListView(FullyActivatedUserMixin, ListView):
    model = Request
    template_name = "pages/requests/request_list.html"
    context_object_name = "requests"
    paginate_by = 10

    @cached_property
    def company(self):
        company_id = self.kwargs.get("company_id")
        if company_id:
            return get_object_or_404(Company, id=company_id, is_deleted=False)
        return None

    def user_test_func(self):
        user = self.request.user

        if not user.is_authenticated or not user.is_fully_activated:
            return False

        if self.company:
            if user.is_superuser or user == self.company.employer:
                return True

            # Set denial message and redirect target
            self.permission_denied_message = (
                "You don't have permission to view this company's requests."
            )
            self.permission_denied_redirect_url = "requests:list"
            return False

        return True  # fallback for self requests view

    def get_queryset(self):
        if self.company:
            # Only show pending requests for employers
            return Request.objects.filter(
                company=self.company, is_deleted=False
            ).order_by("-created_at")
        else:
            return Request.objects.filter(
                author=self.request.user, is_deleted=False
            ).order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.company:
            context["company"] = self.company
            context["title"] = f"Requests for {self.company.name}"
        else:
            context["title"] = "My Requests"

        return context


class ProcessRequestView(FullyActivatedUserMixin, View):
    @cached_property
    def request_obj(self):
        return get_object_or_404(Request, pk=self.kwargs.get("pk"), is_deleted=False)

    def user_test_func(self):
        # Store custom denial reason
        self.permission_denied_message = (
            "You do not have permission to process this request."
        )
        self.permission_denied_redirect_url = "requests:list"

        return self.request_obj.can_be_processed_by(self.request.user)

    def post(self, request, **kwargs):
        action = request.POST.get("action")
        request_obj = self.request_obj

        if action == "approve":
            # Update request status
            request_obj.status = Request.RequestStatus.APPROVED
            request_obj.save()

            # If it's a join request, update the user's workplace
            if request_obj.type == Request.RequestType.JOIN and request_obj.author:
                if request_obj.author.type == "employee":
                    request_obj.author.workplace = request_obj.company
                    request_obj.author.save()
                    messages.success(request, "Join request approved successfully.")
                else:
                    messages.warning(
                        request, "Request type is not valid for this author."
                    )

            # If it's a claim request, update the company's employer
            elif request_obj.type == Request.RequestType.CLAIM and request_obj.author:
                if request_obj.author.type == "employer":
                    company = request_obj.company
                    # If the company already has an employer, handle ownership transfer
                    if company.employer:
                        old_employer = company.employer
                        old_employer.company = None
                        old_employer.save()
                        # Notify the old employer about the ownership change
                        # TODO: send notification to old employer

                        # Create a system message or notification for the old employer
                        messages.info(
                            request,
                            f"The previous owner ({old_employer.get_full_name()}) "
                            f"has been notified of this ownership change.",
                        )

                    # Set the new employer
                    company.employer = request_obj.author
                    company.save()

                    messages.success(
                        request,
                        f"Claim request approved. {request_obj.author.get_full_name()} "
                        f"is now the employer of {company.name}.",
                    )
                else:
                    messages.warning(
                        request, "Request type is not valid for this author."
                    )
            else:
                messages.success(request, "Request approved successfully.")

        elif action == "reject":
            request_obj.status = Request.RequestStatus.REJECTED
            request_obj.save()
            messages.success(request, "Request rejected successfully.")

        # Redirect back to the request detail page
        return redirect("requests:detail", pk=request_obj.pk)


class CreateRequestReplyView(FullyActivatedUserMixin, CreateView):
    model = RequestReply
    form_class = RequestReplyForm

    @cached_property
    def request_obj(self):
        return get_object_or_404(
            Request, pk=self.kwargs.get("request_id"), is_deleted=False
        )

    def user_test_func(self):
        user = self.request.user

        self.permission_denied_message = (
            "You do not have permission to reply to this request."
        )
        self.permission_denied_redirect_url = "requests:list"

        return (
            user == self.request_obj.author or user == self.request_obj.company.employer
        )

    def get_success_url(self):
        return reverse("requests:detail", kwargs={"pk": self.kwargs.get("request_id")})

    def form_valid(self, form):
        form.instance.request = self.request_obj
        form.instance.author = self.request.user

        messages.success(self.request, "Your reply has been posted successfully.")
        response = super().form_valid(form)

        print(
            "Attached to:",
            ContentType.objects.get_for_model(RequestReply).model,
            self.object.id,
        )
        file = self.request.FILES.get("upload_document")
        if file:
            SecureFile.objects.create(
                content_type=ContentType.objects.get_for_model(RequestReply),
                object_id=self.object.id,
                file=file,
                uploaded_by=self.request.user,
            )
            messages.success(self.request, "Document uploaded successfully.")

        return response


class CancelRequestView(FullyActivatedUserMixin, View):
    @cached_property
    def request_obj(self):
        return get_object_or_404(Request, pk=self.kwargs.get("pk"), is_deleted=False)

    def user_test_func(self):
        self.permission_denied_message = (
            "You do not have permission to cancel this request."
        )
        self.permission_denied_redirect_url = "requests:list"
        return self.request.user == self.request_obj.author

    def post(self, request, *args, **kwargs):
        self.request_obj.delete()  # uses your model's soft delete
        messages.success(request, "Your request has been cancelled.")
        return redirect("requests:list")


class ManageClaimsView(FullyActivatedUserMixin, ListView):
    """View for admins to manage company claim requests"""

    template_name = "pages/requests/manage_claims.html"
    context_object_name = "requests"
    paginate_by = 10

    def user_test_func(self):
        # Only superusers can access this view
        self.permission_denied_message = (
            "You do not have permission to view these requests."
        )
        self.permission_denied_redirect_url = "requests:list"
        return self.request.user.is_superuser

    def get_queryset(self):
        # Get all claim requests
        return Request.objects.filter(
            type="claim",  # Using string value instead of enum
            status="pending",  # Only show pending requests
            is_deleted=False,
        ).order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Manage Company Claims"
        context["description"] = (
            "Review and process requests to claim company ownership"
        )
        return context


class ManageUnclaimedRequestsView(FullyActivatedUserMixin, ListView):
    """View for admins to manage join/other requests sent to unclaimed companies."""

    template_name = "pages/requests/manage_unclaimed.html"
    context_object_name = "requests"
    paginate_by = 10

    def user_test_func(self):
        self.permission_denied_message = (
            "You do not have permission to view these requests."
        )
        self.permission_denied_redirect_url = "dashboard"
        return self.request.user.is_superuser

    def get_queryset(self):
        return (
            Request.objects.filter(
                type__in=["join", "other"],
                status="pending",
                company__employer__isnull=True,
                is_deleted=False,
            )
            .select_related("author", "company")
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Unclaimed Join & Other Requests"
        context["description"] = (
            "Manage requests sent to companies that are not yet claimed by an employer."
        )
        return context
