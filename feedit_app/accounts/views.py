from datetime import timedelta
from enum import Enum

from allauth.account import app_settings as allauth_settings
from allauth.account.forms import ChangePasswordForm
from allauth.account.models import EmailConfirmationHMAC
from allauth.account.utils import (
    complete_signup,
    get_user_model,
    perform_login,
    send_email_confirmation,
)
from allauth.account.views import (
    ConfirmEmailView,
    PasswordResetView,
)
from allauth.mfa.base.views import AuthenticateView
from app.mixins import FullyActivatedUserMixin
from company_requests.models import Request
from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import (
    update_session_auth_hash,
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordResetConfirmView
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.http import Http404
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.timezone import now
from django.views.generic import DetailView, ListView, TemplateView, View

from .forms import (
    CustomLoginForm,
    CustomResetPasswordForm,
    CustomSignupForm,
    UserProfileForm,
)

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
                    if session_data and isinstance(
                        session_data.get("email_verification"), Enum
                    ):
                        session_data["email_verification"] = str(
                            session_data["email_verification"]
                        )
                        request.session["account_login"] = session_data
                except Exception:
                    # Reset corrupted session data
                    request.session["account_login"] = {}

                return perform_login(request, user, redirect_url=self.success_url)

            context = {
                "login_form": login_form,
                "signup_form": signup_form,
            }

        elif "register" in request.POST:
            signup_form = CustomSignupForm(request.POST)
            login_form = CustomLoginForm(request=request)
            if signup_form.is_valid():
                user = signup_form.save(request)
                return complete_signup(
                    request,
                    user,
                    allauth_settings.EMAIL_VERIFICATION,
                    reverse_lazy("account_email_verification_sent"),
                )
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
        request.session.pop(
            "account_mfa_authenticated", None
        )  # ✅ Clear MFA session flag
        auth_logout(request)
        return redirect(self.success_url)


class CustomAuthenticateView(AuthenticateView):
    def form_valid(self, form):
        # ✅ Mark MFA as verified in session
        self.request.session["account_mfa_authenticated"] = True
        # Continue normal flow
        return super().form_valid(form)


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
        success_url = reverse_lazy("account_confirm_success")

        self.object = self.get_object()
        self.object.confirm(request)
        return redirect(success_url)


class EmailVerificationSentView(TemplateView):
    template_name = "pages/account/verification_sent.html"


class ResendEmailVerificationView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        send_email_confirmation(request, request.user)
        return redirect("account_edit")  # or wherever you want to return


class ConfirmSuccessView(TemplateView):
    template_name = "pages/account/email_confirm_success.html"


class ProfileView(UserPassesTestMixin, DetailView):
    template_name = "pages/account/user_profile.html"
    context_object_name = "profile_user"
    model = User

    def get_object(self):
        identifier = self.kwargs.get("identifier")

        if identifier is None:
            # Guest accessing /account/ without being logged in — return None
            if not self.request.user.is_authenticated:
                return None
            return self.request.user

        # Try resolving by integer ID
        if identifier.isdigit():
            try:
                return User.objects.get(pk=int(identifier))
            except User.DoesNotExist:
                pass

        # Fallback: Try resolving by name (e.g., john-doe)
        try:
            parts = identifier.replace("-", " ").split()
            if len(parts) == 2:
                first_name, last_name = parts
                return User.objects.filter(
                    first_name__iexact=first_name.strip(),
                    last_name__iexact=last_name.strip(),
                    is_active=True,
                ).first()
            elif len(parts) == 1:
                return User.objects.filter(
                    first_name__iexact=parts[0].strip(), is_active=True
                ).first()
        except Exception:
            pass

        # Default fallback (safe): self-profile
        return self.request.user

    def test_func(self):
        user = self.get_object()
        viewer = self.request.user

        # Store object early for use in dispatch and context
        self.object = user

        if user and user.can_view_profile(viewer):
            return True

        if not viewer.is_authenticated:
            # Visiting own profile
            if user is None or user == viewer:
                messages.info(
                    self.request,
                    "Please sign in or create an account to view your profile.",
                )
            else:
                messages.info(
                    self.request,
                    "This profile is not public. Please sign in or create an account.",
                )
            self.permission_denied_redirect_url = "account_auth"
        else:
            messages.warning(
                self.request,
                "This profile is private. You don’t have permission to view it.",
            )
        return False

    def handle_no_permission(self):
        return redirect(
            getattr(self, "permission_denied_redirect_url", "account_profile")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_own_profile"] = self.object == self.request.user
        return context


class EditProfileView(LoginRequiredMixin, TemplateView):
    template_name = "pages/account/edit_profile.html"
    success_url = reverse_lazy("dashboard")

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


class DashboardView(FullyActivatedUserMixin, TemplateView):
    """
    Handles the main dashboard view after login.
    """

    template_name = "pages/dashboard.html"  # Template for the actual dashboard

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Thread & mention data (existing logic)
        user_threads = (
            user.threads.filter(parent__isnull=True, is_deleted=False)
            .select_related("company")
            .order_by("-created_at")[:5]
        )  # Get the 5 most recent threads

        # Get threads where the user is mentioned
        # Get all mentions, prioritizing unread ones
        # Don't filter by is_read to show all mentions
        mentions = (
            user.mentions_received.filter(
                thread__is_deleted=False,
            )
            .select_related("thread", "thread__author")
            .order_by("-created_at")[:10]  # Show more mentions
        )

        account_age = timezone.now() - user.created_at
        has_any_threads = user.threads.exists()
        is_new_account = account_age < timedelta(days=7) and not has_any_threads

        # Convert mentions queryset to list for template
        mentions_list = list(mentions)

        context.update(
            {
                "user_threads": user_threads,
                "mentions": mentions_list,
                "thread_count": user_threads.count(),
                "mention_count": len(mentions_list),
                "new_account": is_new_account,
            }
        )

        # === Request Summary ===
        if user.type == "employee":
            user_requests = Request.objects.filter(author=user, is_deleted=False)
            context["my_requests"] = {
                "pending": user_requests.filter(status="pending").count(),
                "approved": user_requests.filter(status="approved").count(),
                "rejected": user_requests.filter(status="rejected").count(),
            }

        elif user.type == "employer":
            user_requests = Request.objects.filter(author=user, is_deleted=False)
            company_requests = (
                Request.objects.filter(
                    company=user.company, status="pending", is_deleted=False
                )
                if getattr(user, "company", None)
                else Request.objects.none()
            )
            context["my_requests"] = {
                "pending": user_requests.filter(status="pending").count(),
                "approved": user_requests.filter(status="approved").count(),
                "rejected": user_requests.filter(status="rejected").count(),
            }
            context["company_requests_count"] = company_requests.count()

        if user.is_superuser:
            claim_requests = Request.objects.filter(
                type="claim", status="pending", is_deleted=False
            ).count()

            unclaimed_requests = Request.objects.filter(
                type__in=["join", "other"],
                status="pending",
                company__employer__isnull=True,
                is_deleted=False,
            ).count()

            context["admin_requests"] = {
                "claims": claim_requests,
                "unclaimed": unclaimed_requests,
            }

        return context


class MentionsListView(FullyActivatedUserMixin, ListView):
    """View for displaying all mentions for the current user."""

    template_name = "pages/account/mentions.html"
    context_object_name = "mentions"
    paginate_by = 20

    def get_queryset(self):
        # Get all mentions for the current user
        return (
            self.request.user.mentions_received.filter(thread__is_deleted=False)
            .select_related("thread", "thread__author")
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        unread_mentions = self.request.user.mentions_received.filter(is_read=False)
        context["unread_count"] = unread_mentions.count()

        # Mark all unread mentions as read when the user views this page
        # Efficient bulk update
        unread_mentions.update(is_read=True, updated_at=now())
        return context
