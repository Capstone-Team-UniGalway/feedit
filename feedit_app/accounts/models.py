from app.base_model import BaseModel
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.contrib.contenttypes.models import ContentType
from django.core.validators import EmailValidator, RegexValidator
from django.db import models
from django.templatetags.static import static


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
        from secure_files.utils import get_secure_file_url

        ct = ContentType.objects.get_for_model(self.__class__)
        secure_file = SecureFile.objects.filter(
            content_type=ct, object_id=self.id, is_deleted=False
        ).first()

        if secure_file and secure_file.file:
            return get_secure_file_url(secure_file)

        return static("images/user_placeholder.png")

    def __str__(self):
        return self.email

    def get_full_name(self):
        return self.first_name + " " + self.last_name

    def can_view_profile(self, viewer):
        """Returns True if `viewer` is allowed to see this user's profile."""

        # Admins can view everything
        if viewer.is_authenticated and viewer.is_superuser:
            return True

        # Public profiles are open to all
        if self.privacy == User.PrivacyType.PUBLIC:
            return True

        # Own profile is always accessible
        if self == viewer:
            return True

        # Guests can only see public
        if not viewer.is_authenticated:
            return False

        # Internal visibility: employee ↔ employee or employee ↔ employer
        if self.privacy == User.PrivacyType.INTERNAL:
            self_company = self.workplace or getattr(self, "company", None)
            viewer_company = viewer.workplace or getattr(viewer, "company", None)

            return (
                self_company and viewer_company and self_company.id == viewer_company.id
            )

        # Private visibility: only employer of user's company can view
        if self.privacy == User.PrivacyType.PRIVATE:
            return (
                self.workplace
                and viewer.type == User.UserType.EMPLOYER
                and getattr(viewer, "company", None)
                and viewer.company.id == self.workplace.id
            )

        return False
