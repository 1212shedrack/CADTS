"""
ambulance_system/urls.py
Main URL configuration for CADTS
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [
    # Django admin (superuser panel)
    path("admin/", admin.site.urls),

    # Auth (register, login, logout, profile)
    path("", include("accounts.urls")),

    # User pages
    path("", include("users.urls")),

    # Driver pages
    path("", include("drivers.urls")),

    # Admin pages (ambulances app holds admin views)
    path("", include("ambulances.urls")),

    # Request workflow
    path("", include("requests_app.urls")),

    # Billing
    path("", include("billing.urls")),

    # Root redirect → login
    path("", lambda request: redirect("login_page"), name="root"),
]

# Serve media and static files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
