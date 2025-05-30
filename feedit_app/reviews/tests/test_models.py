import pytest
from django.core.exceptions import ValidationError
from reviews.models import Review, ReviewReply

from .factories import ReviewFactory, ReviewReplyFactory

pytestmark = pytest.mark.django_db


def test_review_factory_creates_valid_instance():
    review = ReviewFactory()
    assert isinstance(review, Review)
    assert 0.0 <= review.rating <= 5.0
    assert review.company is not None
    assert review.user is not None


def test_review_rating_allows_half_steps():
    for rating in [0.0, 0.5, 1.5, 3.0, 4.5, 5.0]:
        review = ReviewFactory(rating=rating)
        assert review.rating == rating


def test_review_rating_rejects_invalid_steps():
    with pytest.raises(ValidationError):
        review = ReviewFactory.build(rating=4.3)
        review.full_clean()


def test_review_str_representation():
    review = ReviewFactory(user=None, rating=3.5)
    assert str(review) == "Review - 3.5/5"


def test_review_reply_links_to_review():
    review = ReviewFactory()
    reply = ReviewReplyFactory(review=review)
    assert isinstance(reply, ReviewReply)
    assert reply.review is not None
    assert reply.employer is not None
    assert reply in review.replies.all()


def test_guest_review_requires_name_when_not_anonymous():
    review = ReviewFactory.create(user=None, guest_name=None, is_anonymous=False)
    with pytest.raises(ValidationError):
        review.full_clean()


def test_guest_review_with_name_is_valid():
    review = ReviewFactory.create(user=None, guest_name="Alice", is_anonymous=False)
    review.full_clean()  # Should not raise


def test_anonymous_review_does_not_require_user_or_name():
    review = ReviewFactory.create(user=None, guest_name=None, is_anonymous=True)
    review.full_clean()  # Should not raise


def test_review_str_handles_anonymous_guest_and_user():
    anon_review = ReviewFactory.create(user=None, guest_name=None, is_anonymous=True)
    assert str(anon_review).startswith("Review by Anonymous")

    guest_review = ReviewFactory.create(
        user=None, guest_name="Diana", is_anonymous=False
    )
    assert str(guest_review) == "Review by Diana - 4.5/5"

    user_review = ReviewFactory.create(is_anonymous=False)
    expected = f"Review by {user_review.user} - 4.5/5"
    assert str(user_review) == expected
