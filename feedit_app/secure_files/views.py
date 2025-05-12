from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, Http404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from django.apps import apps

from .models import SecureFile
from .forms import SecureFileForm


class SecureFileUploadView(LoginRequiredMixin, View):
    """View for handling secure file uploads."""

    def post(self, request, *args, **kwargs):
        # Get content type and object ID from URL parameters
        content_type_id = kwargs.get('content_type_id')
        object_id = kwargs.get('object_id')

        try:
            # Get content type
            content_type = ContentType.objects.get(id=content_type_id)
            # Get the actual object
            content_object = content_type.get_object_for_this_type(id=object_id)
        except (ContentType.DoesNotExist, ValueError):
            messages.error(request, "Invalid content type or object ID")
            return redirect(request.META.get('HTTP_REFERER', '/'))

        # Create form with the file data
        form = SecureFileForm(
            request.POST,
            request.FILES,
            content_object=content_object,
            uploaded_by=request.user
        )

        if form.is_valid():
            secure_file = form.save()
            messages.success(request, "File uploaded successfully")

            # Redirect back to the referring page
            return redirect(request.META.get('HTTP_REFERER', '/'))
        else:
            for error in form.errors.values():
                messages.error(request, error)
            return redirect(request.META.get('HTTP_REFERER', '/'))


class SecureFileDeleteView(LoginRequiredMixin, View):
    """View for deleting secure files."""

    def post(self, request, file_id, *args, **kwargs):
        secure_file = get_object_or_404(SecureFile, id=file_id)

        # Check if user has permission to delete the file
        if secure_file.uploaded_by != request.user and not request.user.is_superuser:
            raise PermissionDenied("You don't have permission to delete this file")

        # Delete the file
        secure_file.delete()

        messages.success(request, "File deleted successfully")
        return redirect(request.META.get('HTTP_REFERER', '/'))


class SecureFileDownloadView(LoginRequiredMixin, View):
    """View for downloading secure files."""

    def get(self, request, file_id, *args, **kwargs):
        secure_file = get_object_or_404(SecureFile, id=file_id)

        # Check if file exists
        if not secure_file.file:
            raise Http404("File not found")

        # Return the file
        response = HttpResponse(
            secure_file.file.read(),
            content_type='application/octet-stream'
        )
        response['Content-Disposition'] = f'attachment; filename="{secure_file.filename}"'
        return response


class JoinRequestFileDownloadView(LoginRequiredMixin, View):
    """View for downloading files attached to JoinRequest objects with proper permission checks."""

    def get(self, request, join_request_id, secure_file_id, *args, **kwargs):
        # Get the Request model
        Request = apps.get_model('requests', 'Request')

        # Get the join request
        join_request = get_object_or_404(
            Request,
            id=join_request_id,
            type=Request.RequestType.JOIN,
            is_deleted=False
        )

        # Get the secure file
        secure_file = get_object_or_404(SecureFile, id=secure_file_id, is_deleted=False)

        # Verify that the secure file is attached to this join request
        content_type = ContentType.objects.get_for_model(Request)
        if secure_file.content_type_id != content_type.id or secure_file.object_id != join_request.id:
            raise Http404("File not found")

        # Check permissions based on user role
        user = request.user

        # Superusers can always access files
        if user.is_superuser:
            # Allow access - superusers can see all files
            pass
        # Check if user is an employee
        elif user.type == 'employee':
            # Employee can only access their own join request files
            if join_request.author != user:
                raise PermissionDenied("You don't have permission to access this file")
        # Check if user is an employer
        elif user.type == 'employer':
            # Employer can only access join request files for their company
            company = join_request.company
            if not company or company.employer != user:
                raise PermissionDenied("You don't have permission to access this file")
        # Other user types cannot access join request files
        else:
            raise PermissionDenied("You don't have permission to access this file")

        # If all checks pass, return the file
        if not secure_file.file:
            raise Http404("File not found")

        response = HttpResponse(
            secure_file.file.read(),
            content_type='application/octet-stream'
        )
        response['Content-Disposition'] = f'attachment; filename="{secure_file.filename}"'
        return response


class ClaimRequestFileDownloadView(LoginRequiredMixin, View):
    """View for downloading files attached to ClaimRequest objects with proper permission checks."""

    def get(self, request, claim_request_id, secure_file_id, *args, **kwargs):
        # Get the Request model
        Request = apps.get_model('requests', 'Request')

        # Get the claim request
        claim_request = get_object_or_404(
            Request,
            id=claim_request_id,
            type=Request.RequestType.CLAIM,
            is_deleted=False
        )

        # Get the secure file
        secure_file = get_object_or_404(SecureFile, id=secure_file_id, is_deleted=False)

        # Verify that the secure file is attached to this claim request
        content_type = ContentType.objects.get_for_model(Request)
        if secure_file.content_type_id != content_type.id or secure_file.object_id != claim_request.id:
            raise Http404("File not found")

        # Check permissions based on user role
        user = request.user

        # Superusers can always access files
        if user.is_superuser:
            # Allow access - superusers can see all files
            pass
        # Check if user is an employer
        elif user.type == 'employer':
            # Employer can only access their own claim request files
            if claim_request.author != user:
                raise PermissionDenied("You don't have permission to access this file")
        # Employees and other user types cannot access claim request files
        else:
            raise PermissionDenied("You don't have permission to access this file")

        # If all checks pass, return the file
        if not secure_file.file:
            raise Http404("File not found")

        response = HttpResponse(
            secure_file.file.read(),
            content_type='application/octet-stream'
        )
        response['Content-Disposition'] = f'attachment; filename="{secure_file.filename}"'
        return response
