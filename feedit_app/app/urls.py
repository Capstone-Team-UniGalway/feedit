"""
URL configuration for app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from accounts.views import DashboardView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import include, path
from django.views.generic import TemplateView
from django.views.static import serve
from django_prometheus.exports import ExportToDjangoView

from .views import WelcomeView

admin.site.login = login_required(admin.site.login)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("companies/", include("companies.urls")),
    path("", WelcomeView.as_view(), name="home"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path(
        "privacy/",
        TemplateView.as_view(template_name="pages/privacy.html"),
        name="privacy",
    ),
    path(
        "report-bug/",
        TemplateView.as_view(template_name="pages/report_bug.html"),
        name="report_bug",
    ),
    path("account/", include("accounts.urls")),
    path("threads/", include("threads.urls")),
    path("reviews/", include("reviews.urls")),
    path("requests/", include("company_requests.urls")),
    path("notifications/", include("notifications.urls")),
    path("uploads/", include("secure_files.urls")),
    path("upload/", include("django_ckeditor_5.urls")),
    path("metrics/", ExportToDjangoView, name="prometheus-metrics"),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# 👇 Only serve /media in development
if settings.ENVIRONMENT == "development":
    urlpatterns += [
        path("media/<path:path>", serve, {"document_root": settings.MEDIA_ROOT}),
    ]
