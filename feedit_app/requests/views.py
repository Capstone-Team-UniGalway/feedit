from django.views.generic import CreateView, ListView, DetailView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType
from app.mixins import FullyActivatedUserMixin
from .models import Request, RequestReply
from .forms import RequestForm, RequestReplyForm
from secure_files.models import SecureFile

class CreateRequestView(FullyActivatedUserMixin, CreateView):
    model = Request
    form_class = RequestForm
    template_name = 'pages/requests/create_request.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company_id = self.kwargs.get('company_id')
        # Import Company model using apps to avoid circular imports
        from django.apps import apps
        Company = apps.get_model('companies', 'Company')
        context['company'] = get_object_or_404(Company, id=company_id)
        return context

    def get_initial(self):
        initial = super().get_initial()
        # Pre-fill the form with join request type
        initial['type'] = Request.RequestType.JOIN
        initial['title'] = f"Request to join {self.get_company().name}"
        return initial

    def get_company(self):
        company_id = self.kwargs.get('company_id')
        # Import Company model using apps to avoid circular imports
        from django.apps import apps
        Company = apps.get_model('companies', 'Company')
        return get_object_or_404(Company, id=company_id)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.company_id = self.kwargs.get('company_id')

        # Use the type selected in the form
        request_type = form.cleaned_data.get('type')

        if request_type == Request.RequestType.CLAIM:
            # Ensure only employers can make claim requests
            if self.request.user.type != 'employer':
                messages.error(self.request, "Only employers can claim companies.")
                return self.form_invalid(form)
            messages.success(self.request, "Your claim request has been submitted and is pending admin approval.")
        else:
            # Default to JOIN type for other cases
            form.instance.type = Request.RequestType.JOIN
            messages.success(self.request, "Your join request has been submitted successfully.")

        # Save the form to create the request object
        response = super().form_valid(form)

        # Handle file upload if provided
        verification_document = self.request.FILES.get('verification_document')
        if verification_document:
            # Get the content type for Request model
            content_type = ContentType.objects.get_for_model(Request)

            # Create a SecureFile instance
            secure_file = SecureFile(
                content_type=content_type,
                object_id=self.object.id,  # self.object is the newly created Request
                file=verification_document,
                uploaded_by=self.request.user
            )

            # Save the secure file
            secure_file.save()

            messages.success(self.request, "Verification document uploaded successfully.")

        return response


class RequestDetailView(FullyActivatedUserMixin, DetailView):
    model = Request
    template_name = 'pages/requests/request_detail.html'
    context_object_name = 'request'

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
            content_type=content_type,
            object_id=request_obj.id,
            is_deleted=False
        )

        context['can_process_request'] = can_process
        context['can_reply'] = can_process or user == request_obj.author
        context['reply_form'] = RequestReplyForm()
        context['files'] = files

        return context


class RequestListView(FullyActivatedUserMixin, ListView):
    model = Request
    template_name = 'pages/requests/request_list.html'
    context_object_name = 'requests'
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        # Show requests created by the current user
        return Request.objects.filter(
            author=user,
            is_deleted=False
        ).order_by('-created_at')


class CompanyRequestListView(FullyActivatedUserMixin, ListView):
    model = Request
    template_name = 'pages/requests/request_list.html'
    context_object_name = 'requests'
    paginate_by = 10

    def get_queryset(self):
        company_id = self.kwargs.get('company_id')
        # Import Company model using apps to avoid circular imports
        from django.apps import apps
        Company = apps.get_model('companies', 'Company')
        company = get_object_or_404(Company, id=company_id)

        # Only company employer can see company requests
        if self.request.user != company.employer:
            return Request.objects.none()

        return Request.objects.filter(
            company=company,
            is_deleted=False
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['company_view'] = True
        return context


class ProcessRequestView(FullyActivatedUserMixin, View):
    def post(self, request, **kwargs):
        request_obj = get_object_or_404(Request, pk=kwargs.get('pk'), is_deleted=False)

        # Check if user is authorized to process this request
        # Only company employers can process join requests
        if request_obj.type == Request.RequestType.JOIN:
            if request.user != request_obj.company.employer:
                messages.error(request, "You don't have permission to process this request.")
                return redirect('dashboard')
        # Only superusers can process claim requests
        elif request_obj.type == Request.RequestType.CLAIM:
            if not request.user.is_superuser:
                messages.error(request, "Only administrators can process claim requests.")
                return redirect('dashboard')

        action = request.POST.get('action')

        if action == 'approve':
            # Update request status
            request_obj.status = Request.RequestStatus.APPROVED
            request_obj.save()

            # If it's a join request, update the user's workplace
            if request_obj.type == Request.RequestType.JOIN and request_obj.author:
                request_obj.author.workplace = request_obj.company
                request_obj.author.save()
                messages.success(request, f"Join request approved successfully.")
            # If it's a claim request, update the company's employer
            elif request_obj.type == Request.RequestType.CLAIM and request_obj.author:
                if request_obj.author.type == 'employer':
                    company = request_obj.company
                    # If the company already has an employer, remove that association
                    if company.employer:
                        old_employer = company.employer
                        # We can't directly set company to None because it's a OneToOneField
                        # The relationship will be automatically removed when we set a new employer

                    # Set the new employer
                    company.employer = request_obj.author
                    company.save()

                    messages.success(request, f"Claim request approved. {request_obj.author.get_full_name()} is now the employer of {company.name}.")
                else:
                    messages.warning(request, "Claim approved but the user is not an employer type.")
            else:
                messages.success(request, f"Request approved successfully.")

        elif action == 'reject':
            request_obj.status = Request.RequestStatus.REJECTED
            request_obj.save()
            messages.success(request, f"Request rejected successfully.")

        # Redirect back to the request detail page
        return redirect('requests:detail', pk=request_obj.pk)


class CreateRequestReplyView(FullyActivatedUserMixin, CreateView):
    model = RequestReply
    form_class = RequestReplyForm

    def get_success_url(self):
        return reverse('requests:detail', kwargs={'pk': self.kwargs.get('request_id')})

    def form_valid(self, form):
        request_obj = get_object_or_404(Request, pk=self.kwargs.get('request_id'), is_deleted=False)

        # Check if user can reply (either the author or the company employer)
        if self.request.user != request_obj.author and self.request.user != request_obj.company.employer:
            messages.error(self.request, "You don't have permission to reply to this request.")
            return redirect('dashboard')

        form.instance.request = request_obj
        form.instance.author = self.request.user

        messages.success(self.request, "Your reply has been posted successfully.")
        return super().form_valid(form)
