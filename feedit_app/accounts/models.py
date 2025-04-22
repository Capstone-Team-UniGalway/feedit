from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.templatetags.static import static
from django.db import models
from app.base_model import BaseModel
from django.core.validators import EmailValidator, RegexValidator
from django.contrib.contenttypes.models import ContentType


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class ActiveUserManager(UserManager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


# Custom User model with role and MFA support
class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    class UserType(models.TextChoices):
        EMPLOYEE = "employee", "Employee"
        EMPLOYER = "employer", "Employer"

    class PrivacyType(models.TextChoices):
        PUBLIC = "public", "Public"
        PRIVATE = "private", "Private"
        INTERNAL = "internal", "Internal"

    type = models.CharField(
        max_length=10, choices=UserType.choices, default=UserType.EMPLOYEE
    )
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(
        unique=True,
        validators=[EmailValidator(message="Enter a valid email address.")],
    )
    job_title = models.CharField(
        max_length=100,
        validators=[
            RegexValidator(
                regex=r"^[a-zA-Z\s]{1,100}$",
                message=(
                    "Job title must only contain letters and spaces "
                    "(max 100 characters)."
                ),
            )
        ],
        blank=True,
        null=True,
    )
    workplace = models.ForeignKey(
        "companies.Company",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employees",
    )
    bio = models.TextField(blank=True, null=True)
    privacy = models.CharField(
        max_length=10, choices=PrivacyType.choices, default=PrivacyType.PUBLIC
    )
    mfa_enabled = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=False)

    objects = ActiveUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    def __str__(self):
        return self.email

    def get_full_name(self):
        return self.first_name + " " + self.last_name

    @property
    def profile_incomplete(self):
        return not self.job_title or not self.bio

    @property
    def profile_picture(self):
        from secure_files.models import SecureFile

        ct = ContentType.objects.get_for_model(self.__class__)
        secure_file = SecureFile.objects.filter(
            content_type=ct, object_id=self.id
        ).first()

        if secure_file and secure_file.file:
            return secure_file.file.url

        return static("images/user_placeholder.png")
