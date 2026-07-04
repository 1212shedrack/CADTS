# accounts/views.py
# Authentication views: Register, Login, Logout, Profile

from django.shortcuts import render, redirect
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status

from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    UserRegisterSerializer,
    DriverRegisterSerializer,
    LoginSerializer,
    UserProfileSerializer,
)
from .models import CustomUser
import re


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def get_tokens_for_user(user):
    """Generate JWT access and refresh tokens for a given user."""
    refresh = RefreshToken.for_user(user)
    refresh["role"] = user.role
    refresh["full_name"] = user.full_name
    return {
        "refresh": str(refresh),
        "access":  str(refresh.access_token),
    }


# ─────────────────────────────────────────────────────────────────────────────
# API VIEWS
# ─────────────────────────────────────────────────────────────────────────────
class UserRegisterAPIView(APIView):
    """POST /api/auth/register/user/ — Register a new citizen user."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user   = serializer.save()
            tokens = get_tokens_for_user(user)
            return Response({
                "message": "Registration successful.",
                "user": {
                    "id":         user.id,
                    "full_name":  user.full_name,
                    "email":      user.email,
                    "role":       user.role,
                },
                **tokens,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DriverRegisterAPIView(APIView):
    """POST /api/auth/register/driver/ — Register a new driver (pending approval)."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = DriverRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "message": "Driver registration submitted. Awaiting admin approval.",
                "user": {
                    "id":        user.id,
                    "full_name": user.full_name,
                    "email":     user.email,
                    "role":      user.role,
                },
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(APIView):
    """POST /api/auth/login/ — Authenticate and receive JWT tokens."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user   = serializer.validated_data["user"]
            tokens = get_tokens_for_user(user)
            return Response({
                "message": "Login successful.",
                "user": {
                    "id":          user.id,
                    "full_name":   user.full_name,
                    "email":       user.email,
                    "role":        user.role,
                    "is_approved": user.is_approved,
                },
                **tokens,
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutAPIView(APIView):
    """POST /api/auth/logout/ — Blacklist refresh token."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            pass  # Token already invalid — still respond success
        return Response({"message": "Logged out successfully."}, status=status.HTTP_200_OK)


class ProfileAPIView(APIView):
    """GET/PATCH /api/auth/profile/ — View and update logged-in user's profile."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────────────────────────────────────────
# HTML PAGE VIEWS
# ─────────────────────────────────────────────────────────────────────────────
def login_page(request):
    """Render the login HTML page."""
    return render(request, "accounts/login.html")


def user_register_page(request):
    """Render the user registration HTML page."""
    return render(request, "user/register.html")


def driver_register_page(request):
    """Render the driver registration HTML page."""
    return render(request, "driver/register.html")


def logout_view(request):
    """Log out session user and redirect to login."""
    auth_logout(request)
    return redirect("login_page")


def forgot_password_page(request):
    """Render the forgot password HTML page."""
    return render(request, "accounts/forgot_password.html")


# ─────────────────────────────────────────────────────────────────────────────
# PASSWORD RESET API
# ─────────────────────────────────────────────────────────────────────────────
class ForgotPasswordAPIView(APIView):
    """
    POST /api/auth/forgot-password/
    Body: { email, new_password, confirm_password }
    Resets the password for any registered user by email.
    No email server required — admin/user can reset directly.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email           = request.data.get('email', '').strip().lower()
        new_password    = request.data.get('new_password', '')
        confirm_password= request.data.get('confirm_password', '')

        if not email:
            return Response({'error': 'Email address is required.'}, status=400)

        if not new_password:
            return Response({'error': 'New password is required.'}, status=400)

        if new_password != confirm_password:
            return Response({'error': 'Passwords do not match.'}, status=400)

        # Password strength: min 8 chars, at least one letter and one digit
        if len(new_password) < 8:
            return Response({'error': 'Password must be at least 8 characters.'}, status=400)

        if not re.search(r'[A-Za-z]', new_password) or not re.search(r'\d', new_password):
            return Response({'error': 'Password must contain both letters and numbers.'}, status=400)

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            # Vague message to prevent email enumeration
            return Response({'error': 'No account found with that email address.'}, status=404)

        user.set_password(new_password)
        user.save()

        return Response({'message': 'Password reset successfully. You can now log in with your new password.'}, status=200)
