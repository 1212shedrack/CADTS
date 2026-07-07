# ambulances/urls.py
from django.urls import path
from . import views
from requests_app.views import AdminRequestListView

urlpatterns = [
    # HTML Dashboard Pages
    path('dashboard/admin/',
         views.admin_dashboard,
         name='admin_dashboard'),
    path('dashboard/admin/users/',
         views.admin_users,
         name='admin_users'),
    path('dashboard/admin/drivers/',
         views.admin_drivers,
         name='admin_drivers'),
    path('dashboard/admin/ambulances/',
         views.admin_ambulances,
         name='admin_ambulances'),
    path('dashboard/admin/requests/',
         views.admin_requests,
         name='admin_requests'),
    path('dashboard/admin/reports/',
         views.admin_reports,
         name='admin_reports'),
    path('dashboard/admin/settings/',
         views.admin_settings,
         name='admin_settings'),

    # Ambulance API
    path('api/ambulances/',
         views.AmbulanceListCreateAPIView.as_view(),
         name='api_ambulances'),
    path('api/ambulances/mine/',
         views.DriverMineAPIView.as_view(),
         name='api_ambulance_mine'),
    path('api/ambulances/<int:pk>/',
         views.AmbulanceDetailAPIView.as_view(),
         name='api_ambulance_detail'),
    path('api/ambulances/<int:pk>/assign/',
         views.AmbulanceAssignDriverAPIView.as_view(),
         name='api_ambulance_assign'),

    # Driver API
    path('api/drivers/', views.DriverListAPIView.as_view(),
         name='api_drivers'),
    path('api/drivers/choices/', views.DriverChoicesAPIView.as_view(),
         name='api_driver_choices'),
    path('api/drivers/<int:pk>/approve/', views.DriverApproveAPIView.as_view(),
         name='api_driver_approve'),

    # Admin APIs
    path('api/admin/users/', views.UserListAPIView.as_view(),
         name='api_admin_users'),
    path('api/admin/stats/', views.AdminStatsAPIView.as_view(),
         name='api_admin_stats'),
    path('api/admin/requests/', AdminRequestListView.as_view(),
         name='api_admin_requests'),
]
