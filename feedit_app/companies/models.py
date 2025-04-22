from django.conf import settings
from django.db import models
from app.base_model import BaseModel
from django.core.validators import RegexValidator
from django.contrib.contenttypes.models import ContentType
from django.templatetags.static import static
from django.utils import timezone


# Represents a company entity, either created or claimed
class Company(BaseModel):
    class VerificationStatus(models.TextChoices):
        UNVERIFIED = "unverified", "Unverified"
        PENDING = "pending", "Verification Pending"
        VERIFIED = "verified", "Verified"
    name = models.CharField(
        max_length=255,
        unique=True,
        validators=[
            RegexValidator(
                regex=r"^[a-zA-Z\s-]{1,100}$",
                message="Name must only contain letters, spaces, and hyphens "
                "(max 100 characters).",
            )
        ],
    )
    industry = models.CharField(
        max_length=100,
        blank=True,
        validators=[
            RegexValidator(
                regex=r"^[a-zA-Z\s-]{1,100}$",
                message="Name must only contain letters, spaces, and hyphens "
                "(max 100 characters).",
            )
        ],
    )
    bio = models.TextField(null=True, blank=True)
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    employer = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="company",
    )
    date_founded = models.DateField(null=True, blank=True)
    verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.UNVERIFIED
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_companies"
    )

    class Meta:
        verbose_name = "Company"
        verbose_name_plural = "Companies"

    def __str__(self):
        return self.name + " (" + self.country + ")"

    @property
    def profile_picture(self):
        from secure_files.models import SecureFile

        ct = ContentType.objects.get_for_model(self.__class__)
        secure_file = SecureFile.objects.filter(
            content_type=ct, object_id=self.id
        ).first()

        if secure_file and secure_file.file:
            return secure_file.file.url

        return static("images/company_placeholder.png")

    @property
    def average_rating(self):
        qs = self.reviews.filter(is_deleted=False)
        if not qs.exists():
            return None
        avg = qs.aggregate(avg=models.Avg("rating"))["avg"]
        return round(avg or 0, 1)

    @property
    def is_claimed(self):
        """Check if the company has an employer assigned."""
        return self.employer is not None

    def verify(self, verified_by=None):
        """Mark the company as verified."""
        self.verification_status = self.VerificationStatus.VERIFIED
        self.verified_at = timezone.now()
        self.verified_by = verified_by
        self.save()
        return True


# Represents a request to join a company
class CompanyJoinRequest(BaseModel):
    class RequestStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="join_requests",
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="join_requests",
    )
    status = models.CharField(
        max_length=10,
        choices=RequestStatus.choices,
        default=RequestStatus.PENDING,
    )
    message = models.TextField(blank=True, null=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="processed_requests",
    )

    class Meta:
        verbose_name = "Company Join Request"
        verbose_name_plural = "Company Join Requests"
        unique_together = ["user", "company", "status"]

    def __str__(self):
        return f"{self.user.email} -> {self.company.name} ({self.status})"

    def approve(self, processed_by=None):
        """Approve the join request and update the user's workplace."""
        from django.utils import timezone

        self.status = self.RequestStatus.APPROVED
        self.processed_at = timezone.now()
        self.processed_by = processed_by
        self.save()

        # Update the user's workplace
        self.user.workplace = self.company
        self.user.save()

        return True

    def reject(self, processed_by=None):
        """Reject the join request."""
        from django.utils import timezone

        self.status = self.RequestStatus.REJECTED
        self.processed_at = timezone.now()
        self.processed_by = processed_by
        self.save()

        return True


# Represents a request to claim ownership of a company
class CompanyClaimRequest(BaseModel):
    class RequestStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="company_claim_requests",
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="claim_requests",
    )
    status = models.CharField(
        max_length=10,
        choices=RequestStatus.choices,
        default=RequestStatus.PENDING,
    )
    message = models.TextField(blank=True, null=True, help_text="Explain why you should be the owner of this company")
    verification_document = models.FileField(upload_to='claim_verifications/', null=True, blank=True,
                                           help_text="Upload a document proving your association with this company")
    processed_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="processed_claim_requests",
    )

    class Meta:
        verbose_name = "Company Claim Request"
        verbose_name_plural = "Company Claim Requests"
        unique_together = ["user", "company", "status"]

    def __str__(self):
        return f"{self.user.email} claims {self.company.name} ({self.status})"

    def approve(self, processed_by=None):
        """Approve the claim request and update the company's employer."""
        self.status = self.RequestStatus.APPROVED
        self.processed_at = timezone.now()
        self.processed_by = processed_by
        self.save()

        # Update the company's employer
        self.company.employer = self.user
        self.company.save()

        # Set the user's workplace to this company
        self.user.workplace = self.company
        self.user.save()

        return True

    def reject(self, processed_by=None):
        """Reject the claim request."""
        self.status = self.RequestStatus.REJECTED
        self.processed_at = timezone.now()
        self.processed_by = processed_by
        self.save()

        return True