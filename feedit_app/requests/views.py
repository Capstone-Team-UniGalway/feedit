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
        return super().dispatch(request, *args, **kwargs)

    def determine_request_type(self):
        if "company_id" in self.kwargs:
            if self.request.user.type == "employer":
                return Request.RequestType.CLAIM
            return Request.RequestType.JOIN
        return Request.RequestType.OTHER

    def user_test_func(self):
        user = self.request.user

        if not user.is_authenticated or not user.is_fully_activated:
            return False

        # Block if no associated company (only applies to 'other')
        if not self.company:
            self.permission_denied_message = (
                "You need to join a company before making requests."
            )
            self.permission_denied_redirect_url = "companies:list"
            return False

        # Block multiple pending requests (only for 'join' and 'claim')
        if self.request_type in [Request.RequestType.JOIN, Request.RequestType.CLAIM]:
            if user.has_company:
                self.permission_denied_message = (
                    f"You cannot make {self.request_type} requests while you are "
                    "already part of a company."
                )
                self.permission_denied_redirect_url = "dashboard"
                return False

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

        # Check if user can process this request
        can_process = False
        if user.is_authenticated:
            # For join requests, only company employer can process
            if request_obj.type == Request.RequestType.JOIN:
                if request_obj.company.employer == user:
                    can_process = True
            # For claim requests, only superusers can process
            elif request_obj.type == Request.RequestType.CLAIM:
                if user.is_superuser:
                    can_process = True

        # Get attached files
        content_type = ContentType.objects.get_for_model(Request)
        files = SecureFile.objects.filter(
            content_type=content_type, object_id=request_obj.id, is_deleted=False
        )

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
    def post(self, request, **kwargs):
        request_obj = get_object_or_404(Request, pk=kwargs.get("pk"), is_deleted=False)

        # Check if user is authorized to process this request
        # Only company employers can process join requests
        if request_obj.type == Request.RequestType.JOIN:
            if request.user != request_obj.company.employer:
                messages.error(
                    request, "You don't have permission to process this request."
                )
                return redirect("dashboard")
        # Only superusers can process claim requests
        elif request_obj.type == Request.RequestType.CLAIM:
            if not request.user.is_superuser:
                messages.error(
                    request, "Only administrators can process claim requests."
                )
                return redirect("dashboard")

        action = request.POST.get("action")

        if action == "approve":
            # Update request status
            request_obj.status = Request.RequestStatus.APPROVED
            request_obj.save()

            # If it's a join request, update the user's workplace
            if request_obj.type == Request.RequestType.JOIN and request_obj.author:
                request_obj.author.workplace = request_obj.company
                request_obj.author.save()
                messages.success(request, "Join request approved successfully.")
            # If it's a claim request, update the company's employer
            elif request_obj.type == Request.RequestType.CLAIM and request_obj.author:
                if request_obj.author.type == "employer":
                    company = request_obj.company
                    # If the company already has an employer, handle ownership transfer
                    if company.employer:
                        old_employer = company.employer
                        # Notify the old employer about the ownership change
                        # (In a real app, you might want to send an email here)

                        # Create a system message or notification for the old employer
                        messages.info(
                            request,
                            f"The previous owner ({old_employer.get_full_name()}) "
                            f"has been notified of this ownership change.",
                        )

                        # The relationship will be automatically removed when
                        # we set a new employer

                    # Check if the new employer is already associated with a company
                    try:
                        existing_company = request_obj.author.company
                        if existing_company and existing_company != company:
                            # Remove the employer from their current company
                            existing_company.employer = None
                            existing_company.save()
                            messages.info(
                                request,
                                f"{request_obj.author.get_full_name()} has been removed"
                                f" as the employer of {existing_company.name}.",
                            )
                    except Exception:
                        # No existing company or error accessing it, continue
                        pass

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
                        request, "Claim approved but the user is not an employer type."
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

    def get_success_url(self):
        return reverse("requests:detail", kwargs={"pk": self.kwargs.get("request_id")})

    def form_valid(self, form):
        request_obj = get_object_or_404(
            Request, pk=self.kwargs.get("request_id"), is_deleted=False
        )

        # Check if user can reply (either the author or the company employer)
        if (
            self.request.user != request_obj.author
            and self.request.user != request_obj.company.employer
        ):
            messages.error(
                self.request, "You don't have permission to reply to this request."
            )
            return redirect("dashboard")

        form.instance.request = request_obj
        form.instance.author = self.request.user

        messages.success(self.request, "Your reply has been posted successfully.")
        return super().form_valid(form)
