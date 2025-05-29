from enum import Enum
from datetime import timedelta
import re
from django.utils import timezone
from django.contrib import messages
from django.db import models
from django.http import HttpResponse
from django.views.generic import TemplateView, View, DetailView, ListView
from django.shortcuts import render
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
from allauth.mfa.base.views import AuthenticateView
from .forms import (
    CustomLoginForm,
    CustomSignupForm,
    UserProfileForm,
    CustomResetPasswordForm,
)
from django.http import Http404
from app.mixins import FullyActivatedUserMixin
from requests.models import Request

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


class ProfileView(FullyActivatedUserMixin, DetailView):
    template_name = "pages/account/user_profile.html"
    context_object_name = "user"
    model = User

    def get_object(self):
        # Check if a user ID is provided in the URL
        user_id = self.request.GET.get("user")
        user_name = self.request.GET.get("user_name")

        if user_id:
            try:
                # Try to get the user by ID
                return User.objects.get(id=user_id)
            except (User.DoesNotExist, ValueError):
                pass

        if user_name:
            # Try to find the user by name
            # This is less reliable but needed for backward compatibility
            try:
                if " " in user_name:
                    first_name, last_name = user_name.split(" ", 1)
                    user = User.objects.filter(
                        first_name__iexact=first_name,
                        last_name__iexact=last_name,
                        is_active=True,
                    ).first()
                    if user:
                        return user
                else:
                    # Try first name only
                    user = User.objects.filter(
                        first_name__iexact=user_name, is_active=True
                    ).first()
                    if user:
                        return user
            except Exception:
                pass

        # Default to the current user
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Check if this is the user's own profile
        context["is_own_profile"] = self.object == self.request.user
        return context


class PublicProfileView(FullyActivatedUserMixin, DetailView):
    model = User
    template_name = "pages/account/user_profile.html"
    context_object_name = "user"

    def get(self, request, *args, **kwargs):
        user = self.get_object()
        if not user.can_view_profile(request.user):
            messages.warning(request, "This profile is private.")
            return redirect("account_profile")
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        viewer = self.request.user

        context["is_own_profile"] = user == viewer
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
        # Mark all unread mentions as read when the user views this page
        unread_mentions = self.request.user.mentions_received.filter(is_read=False)
        for mention in unread_mentions:
            mention.mark_as_read()
        return context


class UserSearchView(FullyActivatedUserMixin, View):
    """HTMX-compatible view for searching users (for @mentions)."""

    def get(self, request):
        # Get and sanitize query parameter (for direct queries)
        raw_query = request.GET.get("q", "").strip()

        # Sanitize the query to prevent SQL injection
        query = re.sub(r"[^\w\s@\.-]", "", raw_query)

        # Log if sanitization changed the query (potential attack)
        if query != raw_query:
            print(
                f"WARNING: Query was sanitized from '{raw_query}' to '{query}' - "
                "possible injection attempt"
            )

        # Debug logging
        print(f"[UserSearchView] Raw query parameter: '{raw_query}'")
        print(f"[UserSearchView] Sanitized query: '{query}'")

        selected_user_id = request.GET.get("selected_user")
        if selected_user_id:
            # Ensure selected_user_id is numeric
            if not selected_user_id.isdigit():
                print(
                    f"WARNING: Invalid selected_user_id: '{selected_user_id}' - "
                    "possible injection attempt"
                )
                selected_user_id = None

        selected_name = request.GET.get("selected_name")
        if selected_name:
            # Sanitize selected_name
            selected_name = re.sub(r"[^\w\s@\.-]", "", selected_name)

        # If a user was selected, return an empty response (handled by JavaScript)
        if selected_user_id and selected_name and request.headers.get("HX-Request"):
            # Just return an empty div
            # the selection is handled by JavaScript in the client
            return HttpResponse(
                f'<div id="mention-results-{request.GET.get("id", "content")}" '
                'class="hidden"></div>'
            )

        # Get the current user's company to limit search to company members
        company = None
        if hasattr(request.user, "workplace") and request.user.workplace:
            company = request.user.workplace
        elif hasattr(request.user, "company"):
            company = request.user.company

        # Get the User model
        User = get_user_model()

        # Base queryset
        users_qs = User.objects.filter(is_active=True)

        # Filter by company if available
        if company:
            users_qs = users_qs.filter(
                models.Q(workplace=company) | models.Q(company=company)
            )
            print(f"Filtering by company: {company}")
            print(f"Users in company: {users_qs.count()}")
        else:
            print("No company found for user")

        # Initialize users as empty queryset
        users = User.objects.none()

        # Get the textarea ID
        textarea_id = request.GET.get("id", "content")
        print(f"Textarea ID: {textarea_id}")

        # Check if we have a direct query parameter or mention query
        if query is not None:  # Allow empty string queries
            print(f"[UserSearchView] Processing query: '{query}'")
            # Remove @ symbol if present at the beginning
            if query.startswith("@"):
                query = query[1:]
                print(f"[UserSearchView] Removed @ symbol, query now: '{query}'")

            if query.strip():  # If we have actual search text
                print(f"[UserSearchView] Searching for users matching: '{query}'")
                # Search by name or email
                users = users_qs.filter(
                    models.Q(first_name__icontains=query)
                    | models.Q(last_name__icontains=query)
                    | models.Q(email__icontains=query)
                ).exclude(id=request.user.id)[
                    :10
                ]  # Limit to 10 results, exclude current user
                print(f"[UserSearchView] Found {users.count()} users matching query")
            else:
                # Empty query - show some default users (first few in company)
                print("[UserSearchView] Empty query - showing default users")
                users = users_qs.exclude(id=request.user.id)[:5]
                print(f"[UserSearchView] Showing {users.count()} default users")
        else:
            # Try to extract from full text
            raw_full_text = request.GET.get(textarea_id, "")

            # Sanitize the full text to prevent SQL injection
            full_text = re.sub(r"[^\w\s@\.\-,;:\'\"?!()]", "", raw_full_text)

            # Log if sanitization changed the text (potential attack)
            if full_text != raw_full_text:
                print("WARNING: Full text was sanitized - possible injection attempt")
                print(f"Original: '{raw_full_text}'")
                print(f"Sanitized: '{full_text}'")

            print(f"Full text: '{full_text}'")

            # Check if there's an @ symbol in the text
            at_index = full_text.rfind("@")
            if at_index >= 0:
                # Extract the text after the @ symbol
                cursor_pos = len(full_text)  # Assume cursor is at the end
                raw_mention_text = full_text[at_index + 1 : cursor_pos].strip()

                # Sanitize the mention text
                mention_text = re.sub(r"[^\w\s@\.-]", "", raw_mention_text)

                # Only search if we have an @ symbol
                print(
                    f"Found @ symbol at position {at_index}, mention text: "
                    f"'{mention_text}'"
                )

                # Search by name or email
                users = users_qs.filter(
                    models.Q(first_name__icontains=mention_text)
                    | models.Q(last_name__icontains=mention_text)
                    | models.Q(email__icontains=mention_text)
                ).exclude(id=request.user.id)[
                    :10
                ]  # Limit to 10 results, exclude current user

                # Set query for the template
                query = mention_text
            else:
                print("No @ symbol found in text")

        # Log the results
        print(f"Found {users.count()} matching users")
        for user in users:
            print(f"- {user.get_full_name()} ({user.email})")

        # Always return HTML for the dropdown
        print(f"Headers: {dict(request.headers)}")
        print(f"Query: {query}")
        print(f"Users: {[user.get_full_name() for user in users]}")

        # Check if the query starts with @
        if query and query.startswith("@"):
            query = query[1:]  # Remove the @ symbol

        # Always render the HTML template
        return render(
            request,
            "components/user_search_results_tailwind.html",
            {"users": users, "query": query},
        )
