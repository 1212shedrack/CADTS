# users/views.py
from django.shortcuts import render


def user_dashboard(request):
    return render(request, 'user/dashboard.html')


def user_map(request):
    return render(request, 'user/map.html')


def user_ambulances(request):
    return render(request, 'user/ambulances.html')


def user_hospitals(request):
    return render(request, 'user/hospitals.html')


def user_track(request):
    return render(request, 'user/track.html')


def user_profile(request):
    return render(request, 'user/profile.html')


def user_history(request):
    return render(request, 'user/history.html')


def user_billing(request):
    return render(request, 'user/billing.html')
