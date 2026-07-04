# users/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/user/', views.user_dashboard,
         name='user_dashboard'),
    path('dashboard/user/map/', views.user_map,
         name='user_map'),
    path('dashboard/user/ambulances/', views.user_ambulances,
         name='user_ambulances'),
    path('dashboard/user/hospitals/', views.user_hospitals,
         name='user_hospitals'),
    path('dashboard/user/track/', views.user_track,
         name='user_track'),
    path('dashboard/user/profile/', views.user_profile,
         name='user_profile'),
    path('dashboard/user/history/', views.user_history,
         name='user_history'),
    path('dashboard/user/billing/', views.user_billing,
         name='user_billing'),
]
