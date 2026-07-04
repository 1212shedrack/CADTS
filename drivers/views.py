# drivers/views.py
from django.shortcuts import render


def driver_dashboard(request):
    return render(request, 'driver/dashboard.html')


def driver_profile(request):
    return render(request, 'driver/profile.html')


def driver_history(request):
    return render(request, 'driver/history.html')


def driver_current_request(request):
    return render(request, 'driver/current_request.html')
