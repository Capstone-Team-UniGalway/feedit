from django.conf import settings
from django.db import models
from django_ckeditor_5.fields import CKEditor5Field
from django.contrib.auth.models import AbstractUser

# Anonymous or named reviews about companies
class Review(models.Model):
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    content = CKEditor5Field()
    is_anonymous = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


# Employer replies to reviews
class ReviewReply(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="replies")
    employer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="review_replies")
    content = CKEditor5Field()
    created_at = models.DateTimeField(auto_now_add=True)