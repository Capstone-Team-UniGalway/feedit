from django.contrib import admin

from .models import Mention, Thread

# Register your models here.
admin.site.register([Thread, Mention])
