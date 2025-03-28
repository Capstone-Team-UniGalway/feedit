from django.db import models
from django.utils.timezone import now

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)  # Set only on creation
    updated_at = models.DateTimeField(auto_now=True)      # Update on every save
    deleted_at = models.DateTimeField(null=True, blank=True)                  # Update on every delete
    is_deleted = models.BooleanField(default=False)
    
    def delete(self, *args, **kwargs):
        """Soft delete the user instead of removing it from the database."""
        self.is_deleted = True
        self.deleted_at = now()
        self.save()

    class Meta:
        abstract = True