# requests_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # User endpoints
    path(
        'api/requests/',
        views.UserRequestListCreateView.as_view(),
        name='api_request_create',
    ),
    path(
        'api/requests/my/',
        views.UserRequestListCreateView.as_view(),
        name='api_request_my',
    ),
    path(
        'api/requests/<int:pk>/',
        views.UserRequestDetailView.as_view(),
        name='api_request_detail',
    ),
    path(
        'api/requests/<int:pk>/cancel/',
        views.UserCancelRequestView.as_view(),
        name='api_request_cancel',
    ),

    # Driver endpoints
    path(
        'api/requests/driver/',
        views.DriverRequestListView.as_view(),
        name='api_driver_requests',
    ),
    path(
        'api/requests/driver/current/',
        views.DriverCurrentRequestView.as_view(),
        name='api_driver_current',
    ),
    path(
        'api/requests/<int:pk>/accept/',
        views.DriverAcceptRequestView.as_view(),
        name='api_request_accept',
    ),
    path(
        'api/requests/<int:pk>/reject/',
        views.DriverRejectRequestView.as_view(),
        name='api_request_reject',
    ),
    path(
        'api/requests/<int:pk>/status/',
        views.DriverUpdateStatusView.as_view(),
        name='api_request_status',
    ),
]
