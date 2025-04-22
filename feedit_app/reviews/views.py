from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Review, ReviewReply
from companies.models import Company


@login_required
def create_review(request, company_id):
    """View for creating a new review."""
    company = get_object_or_404(Company, pk=company_id, is_deleted=False)

    if request.method == "POST":
        # Debug information
        print(f"POST data: {request.POST}")

        try:
            # Get form data directly from POST
            rating = int(request.POST.get("rating", 5))
            content = request.POST.get("content", "")
            is_anonymous = request.POST.get("is_anonymous") == "on"

            print(
                f"Parsed data - Rating: {rating}, Content: {content}, "
                f"Anonymous: {is_anonymous}"
            )

            # Validate rating
            if rating < 1 or rating > 5:
                messages.error(request, "Rating must be between 1 and 5 stars.")
                return render(
                    request, "pages/reviews/review_form.html", {"company": company}
                )

            # Validate content
            if not content.strip():
                messages.error(request, "Review content is required.")
                return render(
                    request, "pages/reviews/review_form.html", {"company": company}
                )

            # Create and save the review
            review = Review(
                company=company,
                user=None if is_anonymous else request.user,
                rating=rating,
                content=content,
                is_anonymous=is_anonymous,
            )
            review.save()
            print(f"Review saved with ID: {review.id}")

            messages.success(request, "Your review has been submitted successfully!")
            return redirect("companies:detail", pk=company_id)

        except Exception as e:
            print(f"Error: {str(e)}")
            messages.error(request, f"Error submitting review: {str(e)}")

    context = {"company": company}
    return render(request, "pages/reviews/review_form.html", context)


@login_required
def create_review_reply(request, review_id):
    """View for replying to a review."""
    review = get_object_or_404(Review, pk=review_id, is_deleted=False)
    company = review.company

    # Check if user is the employer of the company
    if request.user != company.employer and not request.user.is_superuser:
        messages.error(request, "Only the company employer can reply to reviews.")
        return redirect("companies:detail", pk=company.id)

    if request.method == "POST":
        try:
            # Get form data directly from POST
            content = request.POST.get("content", "")

            # Validate content
            if not content.strip():
                messages.error(request, "Reply content is required.")
                return render(
                    request,
                    "pages/reviews/review_reply_form.html",
                    {"review": review, "company": company},
                )

            # Create and save the reply
            reply = ReviewReply(review=review, employer=request.user, content=content)
            reply.save()

            messages.success(request, "Your reply has been posted successfully!")
            return redirect("companies:detail", pk=company.id)

        except Exception as e:
            messages.error(request, f"Error submitting reply: {str(e)}")

    context = {"review": review, "company": company}
    return render(request, "pages/reviews/review_reply_form.html", context)
