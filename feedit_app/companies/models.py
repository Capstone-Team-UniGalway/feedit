from django.conf import settings
from django.db import models
from ckeditor.fields import RichTextField
from django.contrib.auth.models import AbstractUser

# Represents a company entity, either created or claimed
class Company(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="companies_created")
    claimed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="companies_claimed")
    is_claimed = models.BooleanField(default=False)
    details = models.TextField(blank=True)


# Tracks membership of users in companies with approval status
class CompanyMembership(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
    ]
    ROLE_CHOICES = [
        ("employee", "Employee"),
        ("employer", "Employer"),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="company_memberships")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="memberships")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    proof_document = models.FileField(upload_to="proofs/", blank=True, null=True)
    role_in_company = models.CharField(max_length=10, choices=ROLE_CHOICES)
