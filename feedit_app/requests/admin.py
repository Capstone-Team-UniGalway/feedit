from django.contrib import admin
from .models import Request, RequestReply

# Register your models here.
admin.site.register(Request)
admin.site.register(RequestReply)
