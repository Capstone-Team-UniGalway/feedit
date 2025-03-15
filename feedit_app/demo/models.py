from django.db import models

# Create your models here.
class Demo(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField()
    phone_no = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ['-amount']  # Sort by amount descending

    def __str__(self):
        return self.name
