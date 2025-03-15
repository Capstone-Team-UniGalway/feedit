from django.contrib import admin

# Register your models here.
from .models import Demo

@admin.register(Demo)
class DemoAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'phone_no', 'amount')
    search_fields = ('name', 'address')
