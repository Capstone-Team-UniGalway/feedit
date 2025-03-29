from django.db import models
from django.utils.timezone import now


class BaseModel(models.Model):
    """Model interface with timestamps and soft delete"""

    # Set only on creation
    created_at = models.DateTimeField(auto_now_add=True)
    # Update on every save
    updated_at = models.DateTimeField(auto_now=True)
    # Update on every delete
    deleted_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    def delete(self, *args, **kwargs):
        """Soft delete the user instead of removing it from the database."""
        self.is_deleted = True
        self.deleted_at = now()
        self.save()

    class Meta:
        abstract = True
