from app.mixins import FullyActivatedUserMixin, SuperuserBypassMixin
from companies.models import Company
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views import View
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView

from .forms import ReviewForm, ReviewReplyForm
from .models import Review, ReviewReply


class CreateReviewView(SuperuserBypassMixin, CreateView):
    http_method_names = ["get", "post"]
    model = Review
    form_class = ReviewForm
    template_name = "pages/reviews/review_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.company = get_object_or_404(
            Company, pk=self.kwargs["company_id"], is_deleted=False
        )
        return super().dispatch(request, *args, **kwargs)

    def user_test_func(self):
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


class CreateReviewReplyView(FullyActivatedUserMixin, CreateView):
    http_method_names = ["get", "post"]
    model = ReviewReply
    form_class = ReviewReplyForm
    template_name = "pages/reviews/review_reply_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.review = get_object_or_404(
            Review, pk=self.kwargs["review_id"], is_deleted=False
        )
        self.company = self.review.company
        return super().dispatch(request, *args, **kwargs)

    def user_test_func(self):
        user = self.request.user
        # Must be employer of the company
        is_employer = user == self.company.employer
        # Must not have already replied
        has_replied = self.review.replies.filter(is_deleted=False).exists()
        return is_employer and not has_replied

    def handle_no_permission(self):
        return render(
            self.request,
            "pages/reviews/review_restricted.html",
            {
                "company": self.company,
                "message": "You are not allowed to reply to this review.",
            },
        )

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


class EmployerReviewsOverviewView(FullyActivatedUserMixin, TemplateView):
    """
    Overview page for employers to see all reviews for their company.
    Only accessible to users who own a company.
    """

    template_name = "pages/reviews/employer_overview.html"

    def user_test_func(self):
        """Ensure user has a company (is an employer)"""
        return hasattr(self.request.user, "company") and self.request.user.company

    def handle_no_permission(self):
        """Redirect to dashboard if user doesn't have permission"""
        messages.error(
            self.request, "You need to own a company to access the reviews overview."
        )
        return redirect("dashboard")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        company = user.company

        # Get all reviews for user's company
        reviews = (
            company.reviews.filter(is_deleted=False)
            .select_related("user")
            .prefetch_related("replies")
            .order_by("-created_at")
        )

        # Add pagination (10 reviews per page)
        paginator = Paginator(reviews, 10)
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        # Calculate statistics
        unreplied_reviews = reviews.filter(replies__isnull=True)
        total_reviews = reviews.count()
        unreplied_count = unreplied_reviews.count()

        # Calculate average rating
        if total_reviews > 0:
            avg_rating = sum(review.rating for review in reviews) / total_reviews
        else:
            avg_rating = 0

        context.update(
            {
                "reviews": page_obj.object_list,
                "page_obj": page_obj,
                "is_paginated": page_obj.has_other_pages(),
                "company": company,
                "unreplied_count": unreplied_count,
                "total_reviews": total_reviews,
                "avg_rating": round(avg_rating, 1),
                "reply_rate": (
                    round(((total_reviews - unreplied_count) / total_reviews * 100), 1)
                    if total_reviews > 0
                    else 0
                ),
            }
        )

        return context
