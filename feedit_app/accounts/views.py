from enum import Enum
from django.views.generic import TemplateView, View
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

        if "login" in request.POST:
            login_form = CustomLoginForm(request=request, data=request.POST)
            signup_form = CustomSignupForm(initial_role=request.GET.get("role"))
            if login_form.is_valid():
                user = login_form.user
                session_data = request.session.get("account_login", {})
                if session_data and isinstance(
                    session_data.get("email_verification"), Enum
                ):
                    session_data["email_verification"] = str(
                        session_data["email_verification"]
                    )
                    request.session["account_login"] = session_data
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
                    request, user, allauth_settings.EMAIL_VERIFICATION, "/dashboard"
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
        success_url = reverse_lazy("dashboard")
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


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "pages/account/user_profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["user"] = user
        # Optional: preload recent activity later
        return context


class EditProfileView(LoginRequiredMixin, TemplateView):
    template_name = "pages/account/edit_profile.html"
    success_url = reverse_lazy("account_edit")

    def get(self, request, *args, **kwargs):
        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        if "update_profile" in request.POST:
            profile_form = UserProfileForm(request.POST, instance=request.user)
            password_form = ChangePasswordForm(user=request.user)
            if profile_form.is_valid():
                profile_form.save()
                # Optional: request.session["toast_success"] = "Profile updated."
                return redirect(self.success_url)
        elif "change_password" in request.POST:
            profile_form = UserProfileForm(instance=request.user)
            password_form = ChangePasswordForm(data=request.POST, user=request.user)
            if password_form.is_valid():
                request.user.set_password(password_form.cleaned_data["password1"])
                request.user.save()
                update_session_auth_hash(request, request.user)  # Keeps user logged in
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
