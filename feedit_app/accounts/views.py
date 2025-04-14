from django.views.generic import TemplateView
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from allauth.account.utils import complete_signup
from allauth.account import app_settings as allauth_settings
from .forms import CustomLoginForm, CustomSignupForm


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
            login_form = CustomLoginForm(data=request.POST, request=request)
            signup_form = CustomSignupForm(initial_role=request.GET.get("role"))
            if login_form.is_valid():
                auth_login(request, login_form.user)
                return redirect(self.success_url)
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
