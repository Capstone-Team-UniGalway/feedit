from django.contrib import admin

from .models import Thread, Mention

# Register your models here.
admin.site.register([Thread, Mention])
