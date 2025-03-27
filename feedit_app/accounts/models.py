from django.conf import settings
from django.db import models
from ckeditor.fields import RichTextField
from django.contrib.auth.models import AbstractUser
# Custom User model with role and MFA support
class User(AbstractUser):
    ROLE_CHOICES = [
        ("employee", "Employee"),
        ("employer", "Employer"),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    is_approved = models.BooleanField(default=False)
    mfa_enabled = models.BooleanField(default=False)


# Profile associated with each user with privacy options
class Profile(models.Model):
    PRIVACY_CHOICES = [
        ("public", "Public"),
        ("private", "Private"),
        ("internal", "Internal"),
    ]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    name = models.CharField(max_length=255)
    job_position = models.CharField(max_length=255)
    bio = models.TextField(blank=True)
    privacy = models.CharField(max_length=10, choices=PRIVACY_CHOICES)
    profile_picture = models.ImageField(upload_to="profiles/", blank=True, null=True)