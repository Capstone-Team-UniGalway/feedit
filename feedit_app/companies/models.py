from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
from app.base_model import BaseModel

# Represents a company entity, either created or claimed
class Company(BaseModel):
    name = models.CharField(max_length=255, unique=True)
    industry = models.CharField(max_length=100, blank=True)
    profile_pic = models.ImageField(upload_to='company_profiles/', null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    employer = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="company")
    date_founded = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return self.name + "(" + self.country + ")"