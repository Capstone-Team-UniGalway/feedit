from django.conf import settings
from django.db import models
from ckeditor.fields import RichTextField

# Group communication threads between employees and employers
class Thread(models.Model):
    VISIBILITY_CHOICES = [
        ("internal", "Internal"),
        ("private", "Private"),
    ]
    TYPE_CHOICES = [
        ("forum", "Forum"),
        ("announcement", "Announcement"),
    ]
    title = models.CharField(max_length=255)
    content = RichTextField()

    # 👇 Use lazy string reference instead of importing Company
    company = models.ForeignKey("companies.Company", on_delete=models.CASCADE, related_name="threads")

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="threads_created")
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# Replies to communication threads
class Reply(models.Model):
    thread = models.ForeignKey("threads.Thread", on_delete=models.CASCADE, related_name="replies")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="thread_replies")
    content = RichTextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Reply by {self.user} on {self.thread}'
