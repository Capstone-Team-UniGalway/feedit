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
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    objects = ActiveUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    @property
    def is_account_verified(self):
        """Returns True if the user's primary email is verified."""
        return self.emailaddress_set.filter(verified=True).exists()

    @property
    def is_profile_complete(self):
        return bool(self.job_title and self.bio)

    @property
    def has_mfa_enabled(self):
        from allauth.mfa.models import Authenticator

        return Authenticator.objects.filter(user=self, type="totp").exists()

    @property
    def is_fully_activated(self):
        return (
            self.is_active
            and self.is_account_verified
            and self.is_profile_complete
            and self.has_mfa_enabled
        )

    @property
    def has_company(self):
        return bool(self.workplace or getattr(self, "company", None))

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

    def __str__(self):
        return self.email

    def get_full_name(self):
        return self.first_name + " " + self.last_name

    def can_view_profile(self, viewer):
        """Returns True if `viewer` is allowed to see this user's profile."""

        # Public profiles are always visible
        if self.privacy == User.PrivacyType.PUBLIC:
            return True

        # Own profile is always visible
        if self == viewer:
            return True

        # Internal profiles — apply fine-grained rules
        if self.privacy == User.PrivacyType.INTERNAL:
            # If either user lacks a company, deny
            if not self.workplace and not hasattr(self, "company"):
                return False
            if not viewer.workplace and not hasattr(viewer, "company"):
                return False

            # Case: viewer is employer, user is employee at same company
            if (
                viewer.type == User.UserType.EMPLOYER
                and self.type == User.UserType.EMPLOYEE
            ):
                return viewer.company and viewer.company == self.workplace

            # Case: viewer is employee, user is employer at same company
            if (
                viewer.type == User.UserType.EMPLOYEE
                and self.type == User.UserType.EMPLOYER
            ):
                return self.company and viewer.workplace == self.company

            # Case: both employees at same company
            if viewer.type == self.type == User.UserType.EMPLOYEE:
                return viewer.workplace and viewer.workplace == self.workplace

        # All other cases denied
        return False
