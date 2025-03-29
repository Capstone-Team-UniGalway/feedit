from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
from app.base_model import BaseModel
from django.core.validators import RegexValidator

# Represents a company entity, either created or claimed
class Company(BaseModel):
    name = models.CharField(max_length=255, unique=True, validators=[RegexValidator(
        regex=r"^[a-zA-Z\s-]{1,100}$",
        message="Name must only contain letters, spaces, and hyphens (max 100 characters)."
    )])
    industry = models.CharField(max_length=100, blank=True, validators=[RegexValidator(
        regex=r"^[a-zA-Z\s-]{1,100}$",
        message="Name must only contain letters, spaces, and hyphens (max 100 characters)."
    )])
    profile_pic = models.ImageField(upload_to='company_profiles/', null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    employer = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="company")
    date_founded = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return self.name + "(" + self.country + ")"