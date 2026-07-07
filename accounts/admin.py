# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ("email", "first_name", "last_name", "role",
                    "is_active", "is_approved", "created_at")
    list_filter = ("role", "is_active", "is_approved", "is_staff")
    search_fields = ("email", "first_name", "last_name", "phone")
    ordering = ("-created_at",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("first_name",
                                      "last_name",
                                      "phone",
                                      "latitude",
                                      "longitude")}),
        ("Role & Status", {"fields": ("role",
                                      "is_active",
                                      "is_approved",
                                      "is_staff",
                                      "is_superuser")}),
        ("Permissions",  {"fields": ("groups",
                                     "user_permissions")}),
        ("Timestamps",   {"fields": ("created_at",
                                     "updated_at")}),
    )
    readonly_fields = ("created_at", "updated_at")

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "first_name",
                       "last_name", "phone",
                       "role", "password1", "password2"),
        }),
    )
