from enum import Enum
from django.conf import settings
from django.contrib import messages
from django.db import models
from django.http import JsonResponse
from django.views.generic import TemplateView, View  # Add TemplateView to imports
from django.shortcuts import render  # Keep render import
from django.contrib.auth import (
    logout as auth_logout,
    update_session_auth_hash,
)
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordResetConfirmView
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.mixins import LoginRequiredMixin
from django.templatetags.static import static
from allauth.account.utils import (
    complete_signup,
    send_email_confirmation,
    get_user_model,
    perform_login,
)
from allauth.account import app_settings as allauth_settings
from allauth.account.models import EmailConfirmationHMAC
from allauth.account.views import (
    ConfirmEmailView,
    PasswordResetView,
)
from allauth.account.forms import ChangePasswordForm
from .forms import (
    CustomLoginForm,
    CustomSignupForm,
    UserProfileForm,
    CustomResetPasswordForm,
)
from django.http import Http404

User = get_user_model()


class AuthRedirectView(View):
    def get(self, request):
        return redirect("account_auth")


class AuthView(TemplateView):
    template_name = "pages/account/login_register.html"
    success_url = reverse_lazy("dashboard")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(self.success_url)
        try:
            return super().dispatch(request, *args, **kwargs)
        except ValueError as e:
            # Handles CSRF token mismatch or form corruption
            return self._render_safe_error(request, e)

    def _render_safe_error(self, request, error_message):
        role = request.GET.get("role")
        context = {
            "login_form": CustomLoginForm(request=request),
            "signup_form": CustomSignupForm(initial_role=role),
            "error_message": error_message,
        }
        return self.render_to_response(context)

    def get(self, request, *args, **kwargs):
        role = request.GET.get("role")
        return self.render_to_response(
            {
                "login_form": CustomLoginForm(request=request),
                "signup_form": CustomSignupForm(initial_role=role),
            }
        )

    def post(self, request, *args, **kwargs):
        context = {}
        role = request.GET.get("role")

        if "login" in request.POST:
            login_form = CustomLoginForm(request=request, data=request.POST)
            signup_form = CustomSignupForm(initial_role=role)
            if login_form.is_valid():
                user = login_form.user
                try:
                    session_data = request.session.get("account_login", {})
                    if not isinstance(session_data, dict):
                        raise ValueError("Session data corrupted")
                    if session_data and isinstance(session_data.get("email_verification"), Enum):
                        session_data["email_verification"] = str(session_data["email_verification"])
                        request.session["account_login"] = session_data
                except Exception:
                    # Reset corrupted session data
                    request.session["account_login"] = {}
                # Store the user's role in the session
                if role:
                    request.session["user_role"] = role
                return perform_login(request, user, redirect_url=self.success_url)

            context = {
                "login_form": login_form,
                "signup_form": signup_form,
            }

        elif "register" in request.POST:
            role = request.GET.get("role")
            signup_form = CustomSignupForm(request.POST)
            login_form = CustomLoginForm(request=request)
            try:
                if signup_form.is_valid():
                    try:
                        user = signup_form.save(request)
                    except ValueError as ve:
                        # Handle duplicate email or similar allauth errors
                        context = {
                            "login_form": login_form,
                            "signup_form": signup_form,
                            "error_message": f"Registration failed: {ve}. If you already have an account, please log in.",
                        }
                        return self.render_to_response(context)
                    # Clear any potentially corrupted login session data after registration
                    if "account_login" in request.session:
                        del request.session["account_login"]
                    if allauth_settings.EMAIL_VERIFICATION != "none":
                        # Store the email in the session for verification bypass
                        request.session['verification_email'] = user.email
                        # Redirect to a dedicated verification sent page
                        return redirect("account_email_verification_sent")
                    return complete_signup(
                        request, user, allauth_settings.EMAIL_VERIFICATION, reverse_lazy("account_edit")
                    )
                else:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Registration failed: {signup_form.errors.as_json()}")
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Registration exception: {str(e)}", exc_info=True)
                context = {
                    "login_form": login_form,
                    "signup_form": signup_form,
                    "error_message": "An unexpected error occurred during registration. Please try again.",
                }
                return self.render_to_response(context)
            context = {
                "login_form": login_form,
                "signup_form": signup_form,
            }

        else:
            context = {
                "login_form": CustomLoginForm(request=request),
                "signup_form": CustomSignupForm(initial_role=request.GET.get("role")),
                "error_message": "Invalid form submission.",
            }

        return self.render_to_response(context)


class LogoutView(LoginRequiredMixin, TemplateView):
    success_url = reverse_lazy("account_auth")

    def get(self, request, *args, **kwargs):
        auth_logout(request)
        return redirect(self.success_url)


class EmailConfirmView(ConfirmEmailView):
    template_name = "pages/account/email_confirm.html"

    def get_object(self, queryset=None):
        key = self.kwargs.get("key")
        confirmation = EmailConfirmationHMAC.from_key(key)
        if not confirmation:
            raise Http404("Invalid confirmation key.")
        if confirmation.email_address.verified:
            return confirmation
        return confirmation

    def post(self, request, *args, **kwargs):
        success_url = reverse_lazy("dashboard")  # Redirect to dashboard after email confirmation
        self.object = self.get_object()
        self.object.confirm(request)
        return redirect(success_url)


class EmailVerificationSentView(TemplateView):
    template_name = "pages/account/verification_sent.html"

    def get(self, request, *args, **kwargs):
        # Store the user's email in the session if available
        if hasattr(request, 'user') and request.user.is_authenticated:
            request.session['verification_email'] = request.user.email

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add a flag to indicate if we're in development mode
        context['is_development'] = True  # Set to False in production

        # Add the email to the context if available in the session
        if 'verification_email' in self.request.session:
            context['email'] = self.request.session['verification_email']

        return context


class BypassEmailVerificationView(View):
    """
    Development-only view that allows bypassing email verification.
    This should be disabled in production environments.
    """
    def get(self, request, *args, **kwargs):
        # Import necessary modules
        from allauth.account.models import EmailAddress
        from django.contrib import messages
        from django.contrib.auth import login

        # Get the email from the session or query parameter
        email = request.GET.get('email')

        if not email:
            # If no email provided, redirect to login page
            messages.error(request, "No email provided for verification bypass.")
            return redirect('account_auth')

        # Find the user by email
        try:
            user = User.objects.get(email=email)

            # Get the email address object
            email_obj = EmailAddress.objects.filter(user=user, email=email).first()

            if email_obj and not email_obj.verified:
                # Mark the email as verified
                email_obj.verified = True
                email_obj.save()

                # Log the user in
                user.backend = 'accounts.backends.SoftDeleteAwareBackend'
                login(request, user)

                # Add a message to inform the user
                messages.success(request, "Email verification bypassed. Please complete your profile.")

                # Redirect to profile edit page
                return redirect('account_edit')
            elif email_obj and email_obj.verified:
                # Email already verified, just log in
                user.backend = 'accounts.backends.SoftDeleteAwareBackend'
                login(request, user)
                return redirect('account_edit')
            else:
                # No email address found for this user
                messages.error(request, "Email address not found in the system.")
                return redirect('account_auth')

        except User.DoesNotExist:
            # User not found
            messages.error(request, "No user found with this email address.")
            return redirect('account_auth')


class ResendEmailVerificationView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        send_email_confirmation(request, request.user)
        return redirect("account_edit")  # or wherever you want to return


class ConfirmSuccessView(TemplateView):
    template_name = "pages/account/email_confirm_success.html"


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "pages/account/user_profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Check if a specific user is requested via URL parameter
        requested_user_id = self.request.GET.get('user')
        User = get_user_model()

        if requested_user_id:
            try:
                # Try to get the requested user
                user = User.objects.get(id=requested_user_id)

                # Check if the user's profile is visible based on privacy settings
                # This is a placeholder - implement actual privacy logic as needed
                if hasattr(user, 'privacy') and user.privacy == 'private' and user != self.request.user:
                    # If private and not the current user, show the current user instead
                    messages.warning(self.request, "This profile is private.")
                    user = self.request.user
            except User.DoesNotExist:
                # If user doesn't exist, show the current user
                messages.error(self.request, "User not found.")
                user = self.request.user
        else:
            # No user specified, show the current user
            user = self.request.user

        # Set a flag to indicate if the user has a profile picture
        context['has_profile_picture'] = hasattr(user, 'profile_picture') and bool(user.profile_picture)

        # Set a flag to indicate if this is the current user's profile
        context['is_own_profile'] = user == self.request.user

        context["user"] = user
        # Optional: preload recent activity later
        return context


class EditProfileView(LoginRequiredMixin, TemplateView):
    template_name = "pages/account/edit_profile.html"
    complete_profile_template = "pages/account/complete_profile.html"
    success_url = reverse_lazy("dashboard")

    def dispatch(self, request, *args, **kwargs):
        # Ensure the user is authenticated before proceeding
        if not request.user.is_authenticated:
            return redirect(f"{settings.LOGIN_URL}?next={request.path}")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        # Check if this is a new user who needs to complete their profile
        user = request.user
        is_profile_incomplete = not user.job_title or not user.bio

        # If coming from email verification or profile is incomplete, show the simplified completion form
        if is_profile_incomplete or 'verification_email' in request.session:
            self.template_name = self.complete_profile_template

            # Clear the verification email from session once used
            if 'verification_email' in request.session:
                del request.session['verification_email']

        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        if "update_profile" in request.POST:
            profile_form = UserProfileForm(request.POST, instance=request.user)
            password_form = ChangePasswordForm(user=request.user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Profile updated successfully.")
                return redirect(self.success_url)
        elif "change_password" in request.POST:
            profile_form = UserProfileForm(instance=request.user)
            password_form = ChangePasswordForm(data=request.POST, user=request.user)
            if password_form.is_valid():
                request.user.set_password(password_form.cleaned_data["password1"])
                request.user.save()
                update_session_auth_hash(request, request.user)  # Keeps user logged in
                messages.success(request, "Password changed successfully.")
                return redirect(self.success_url)
        else:
            # fallback
            profile_form = UserProfileForm(instance=request.user)
            password_form = ChangePasswordForm(user=request.user)

        return self.render_to_response(
            {"form": profile_form, "password_change_form": password_form}
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault("form", UserProfileForm(instance=self.request.user))
        context.setdefault(
            "password_change_form", ChangePasswordForm(user=self.request.user)
        )
        return context


class CloseAccountView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        success_url = reverse_lazy("account_auth")
        user = request.user
        user.is_active = False
        user.delete()
        auth_logout(request)
        return redirect(success_url)


class AuthPasswordResetDonePartial(TemplateView):
    template_name = "components/account/password_reset_done.html"


class CustomPasswordResetFromKeyView(PasswordResetConfirmView):
    template_name = "pages/account/password_reset_from_key.html"
    success_url = "/account/auth"

    def form_valid(self, form):
        user = self.user
        if user and getattr(user, "is_deleted", False):
            return redirect("/account/auth")  # or show token expired message
        return super().form_valid(form)


class CustomPasswordResetView(PasswordResetView):
    form_class = CustomResetPasswordForm
    template_name = "components/account/password_reset_form.html"
    success_url = "/account/password/reset/done/"

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        users = User.objects.filter(
            email__iexact=email, is_active=True, is_deleted=False
        )

        for user in users:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = self.request.build_absolute_uri(
                reverse(
                    "account_reset_password_from_key",
                    kwargs={"uidb64": uid, "token": token},
                )
            )
            site = get_current_site(self.request)

            context = {
                "user": user,
                "password_reset_url": reset_url,
                "site": {"name": site.name, "domain": site.domain},
            }

            subject = "Reset your password"
            body = render_to_string(
                "emails/account/password_reset_key_message.txt", context
            )
            msg = EmailMessage(subject, body, to=[user.email])
            msg.send()

        return redirect(self.success_url)


# --- NEW CLASS-BASED DASHBOARD VIEW ---
class DashboardView(LoginRequiredMixin, View):
    """
    Handles the main dashboard view after login.

    Checks if the user's profile is considered complete. If not,
    redirects to the profile editing page. Otherwise, renders the
    main dashboard template.
    """
    template_name = 'pages/dashboard.html'  # Template for the actual dashboard
    profile_edit_url = reverse_lazy('account_edit')  # URL to redirect to if profile is incomplete

    def get(self, request, *args, **kwargs):
        """Handles GET requests to the dashboard."""
        user = self.request.user

        # --- Determine if profile is incomplete ---
        # Check for essential profile fields that should be completed
        profile_incomplete = False

        # Check job_title (required for both employee and employer)
        if not user.job_title:
            profile_incomplete = True

        # Check bio (required for a complete profile)
        if not user.bio:
            profile_incomplete = True

        # --- Redirect or Render ---
        if profile_incomplete:
            # Profile details are missing, redirect to the edit profile page
            return redirect(self.profile_edit_url)
        else:
            # Profile is complete, render the actual dashboard template
            context = self.get_context_data(**kwargs)
            return render(request, self.template_name, context)

    def get_context_data(self, **kwargs):
        """
        Prepares context data for rendering the dashboard template.
        This method is called only when the profile is considered complete.
        """
        user = self.request.user

        # Get user's threads (excluding replies and deleted threads)
        from threads.models import Thread
        user_threads = Thread.objects.filter(
            author=user,
            parent__isnull=True,  # Only parent threads, not replies
            is_deleted=False      # Only non-deleted threads
        ).order_by('-created_at')[:5]  # Get the 5 most recent threads

        # Get threads where the user is mentioned
        from threads.models import Mention
        mentions = Mention.objects.filter(
            mentioned_user=user,
            is_read=False,         # Only unread mentions
            thread__is_deleted=False  # Only mentions in non-deleted threads
        ).order_by('-created_at')[:5]  # Get the 5 most recent mentions

        context = {
            'user': user,
            'user_threads': user_threads,
            'mentions': mentions,
            'thread_count': user_threads.count(),
            'mention_count': mentions.count(),
        }
        return context


class DirectLoginView(View):
    """A simple direct login view for debugging purposes."""
    def get(self, request):
        return render(request, 'pages/account/direct_login.html')

    def post(self, request):
        email = request.POST.get('email')
        password = request.POST.get('password')

        if not email or not password:
            return render(request, 'pages/account/direct_login.html', {
                'error': 'Please provide both email and password'
            })

        # Get the user model
        User = get_user_model()

        try:
            # Try to get the user by email
            user = User.objects.get(email=email)

            # Print user details for debugging
            print(f"Found user: {user.email}, Active: {user.is_active}, Deleted: {getattr(user, 'is_deleted', False)}")

            # Check if the password is correct
            from django.contrib.auth import authenticate, login
            auth_user = authenticate(request, username=email, password=password)

            if auth_user is not None:
                # Log the user in
                login(request, auth_user)
                print(f"User authenticated successfully: {auth_user.email}")

                # Check if profile is complete
                if not auth_user.job_title or not auth_user.bio:
                    print(f"Profile incomplete, redirecting to edit profile")
                    return redirect('account_edit')
                else:
                    print(f"Profile complete, redirecting to dashboard")
                    return redirect('dashboard')
            else:
                print(f"Authentication failed for user: {email}")
                return render(request, 'pages/account/direct_login.html', {
                    'error': 'Invalid email or password'
                })

        except User.DoesNotExist:
            print(f"User not found: {email}")
            return render(request, 'pages/account/direct_login.html', {
                'error': 'No user found with this email address'
            })


class UserSearchView(LoginRequiredMixin, View):
    """HTMX-compatible view for searching users (for @mentions)."""
    def get(self, request):
        query = request.GET.get('q', '').strip()
        selected_user_id = request.GET.get('selected_user')
        selected_name = request.GET.get('selected_name')

        # If a user was selected, return the mention tag
        if selected_user_id and selected_name and request.headers.get('HX-Request'):
            return render(request, 'components/mention_selected.html', {
                'user_id': selected_user_id,
                'user_name': selected_name
            })

        # Get the current user's company to limit search to company members
        company = None
        if hasattr(request.user, 'workplace') and request.user.workplace:
            company = request.user.workplace

        # Get the User model
        User = get_user_model()

        # Base queryset
        users_qs = User.objects.filter(is_active=True)

        # Filter by company if available
        if company:
            users_qs = users_qs.filter(workplace=company)

        # Initialize users as empty queryset
        users = User.objects.none()

        # Only search if query is at least 2 characters
        if query and len(query) >= 2:
            # Search by name or email
            users = users_qs.filter(
                models.Q(first_name__icontains=query) |
                models.Q(last_name__icontains=query) |
                models.Q(email__icontains=query)
            ).exclude(id=request.user.id)[:10]  # Limit to 10 results, exclude current user

        # Check if this is an HTMX request
        if request.headers.get('HX-Request'):
            # Return HTML for HTMX
            return render(request, 'components/user_search_results.html', {
                'users': users,
                'query': query
            })
        else:
            # For non-HTMX requests, return JSON
            results = [{
                'id': user.id,
                'name': user.get_full_name(),
                'email': user.email,
                'profile_url': f"{reverse('account_profile')}?user={user.id}",
                'has_profile_picture': hasattr(user, 'profile_picture') and bool(user.profile_picture),
            } for user in users]

            return JsonResponse({'users': results})
