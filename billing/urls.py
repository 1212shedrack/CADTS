# billing/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # User
    path(
        'api/billing/my/',
        views.UserBillingListView.as_view(),
        name='api_billing_my',
    ),
    path('api/billing/<int:pk>/',
         views.UserBillingDetailView.as_view(),
         name='api_billing_detail'),

    # Admin
    path('api/billing/admin/',
         views.AdminBillingListView.as_view(),
         name='api_billing_admin'),
    path('api/billing/admin/stats/',
         views.AdminBillingStatsView.as_view(),
         name='api_billing_stats'),
]
