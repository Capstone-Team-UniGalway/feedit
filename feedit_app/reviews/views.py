from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views import View
from django.views.generic.edit import CreateView

from companies.models import Company
from .forms import ReviewForm, ReviewReplyForm
from .models import Review, ReviewReply


class CreateReviewView(UserPassesTestMixin, CreateView):
    http_method_names = ["get", "post"]
    model = Review
    form_class = ReviewForm
    template_name = "pages/reviews/review_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.company = get_object_or_404(
            Company, pk=self.kwargs["company_id"], is_deleted=False
        )
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        user = self.request.user

        # Employer can't review own company
        if user.is_authenticated and user == self.company.employer:
            return False

        # Authenticated user can't review more than once
        if user.is_authenticated:
            return not Review.objects.filter(
                company=self.company, user=user, is_deleted=False
            ).exists()

        # Guests are always allowed (validation logic will handle them in form)
        return True

    def handle_no_permission(self):
        return render(
            self.request,
            "pages/reviews/review_restricted.html",
            {
                "company": self.company,
                "message": "You are not allowed to submit a review for this company.",
            },
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        review = form.save(commit=False)
        review.company = self.company
        review.full_clean()
        review.save()
        messages.success(self.request, "Your review has been submitted successfully!")
        return redirect("companies:detail", pk=self.company.pk)

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below.")
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["company"] = self.company
        return context


class CreateReviewReplyView(LoginRequiredMixin, CreateView):
    http_method_names = ["get", "post"]
    model = ReviewReply
    form_class = ReviewReplyForm
    template_name = "pages/reviews/review_reply_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.review = get_object_or_404(
            Review, pk=self.kwargs["review_id"], is_deleted=False
        )
        self.company = self.review.company

        if request.user != self.company.employer and not request.user.is_superuser:
            messages.error(request, "Only the company employer can reply to reviews.")
            return redirect("companies:detail", pk=self.company.pk)

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        reply = form.save(commit=False)
        reply.review = self.review
        reply.employer = self.request.user
        reply.save()
        messages.success(self.request, "Your reply has been posted successfully!")
        return redirect("companies:detail", pk=self.company.pk)

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below.")
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["review"] = self.review
        context["company"] = self.company
        return context


class ToggleGuestNameFieldView(View):
    def get(self, request):
        is_anonymous = request.GET.get("is_anonymous") == "true"
        user = request.user

        # Only show guest name if unauthenticated AND not anonymous
        show_guest_name = not user.is_authenticated and not is_anonymous

        if show_guest_name:
            form = ReviewForm(user=user)
            html = render_to_string(
                "components/reviews/guest_name_field.html", {"form": form}
            )
            return HttpResponse(html)

        return HttpResponse("")  # Empty response hides guest name field
