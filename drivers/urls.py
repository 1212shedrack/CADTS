# drivers/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path(
        'dashboard/driver/',
        views.driver_dashboard,
        name='driver_dashboard',
    ),
    path(
        'dashboard/driver/profile/',
        views.driver_profile,
        name='driver_profile',
    ),
    path(
        'dashboard/driver/history/',
        views.driver_history,
        name='driver_history',
    ),
    path(
        'dashboard/driver/current/',
        views.driver_current_request,
        name='driver_current',
    ),
]
