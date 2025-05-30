from django.contrib import admin

from .models import Review, ReviewReply

# Register your models here.
admin.site.register(Review)
admin.site.register(ReviewReply)
