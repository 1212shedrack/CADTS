# accounts/permissions.py
# Custom DRF permissions for role-based access control

from rest_framework.permissions import BasePermission


class IsUserRole(BasePermission):
    """Allow access only to users with role='user'."""
    message = "Access restricted to registered users."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == "user"
        )


class IsDriverRole(BasePermission):
    """Allow access only to approved drivers."""
    message = "Access restricted to approved drivers."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == "driver" and
            request.user.is_approved
        )


class IsAdminRole(BasePermission):
    """Allow access only to administrators."""
    message = "Access restricted to administrators."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == "admin"
        )


class IsUserOrAdmin(BasePermission):
    """Allow users and admins."""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role in ("user", "admin")
        )


class IsDriverOrAdmin(BasePermission):
    """Allow approved drivers and admins."""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role in ("driver", "admin")
        )
