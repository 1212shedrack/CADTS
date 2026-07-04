# ambulances/admin.py
from django.contrib import admin
from .models import Ambulance


@admin.register(Ambulance)
class AmbulanceAdmin(admin.ModelAdmin):
    list_display  = ("ambulance_name", "plate_number", "driver_name", "status", "created_at")
    list_filter   = ("status",)
    search_fields = ("ambulance_name", "plate_number")
    ordering      = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Ambulance Info", {"fields": ("ambulance_name", "plate_number", "status")}),
        ("Driver",         {"fields": ("driver",)}),
        ("Location",       {"fields": ("latitude", "longitude")}),
        ("Timestamps",     {"fields": ("created_at", "updated_at")}),
    )

    def driver_name(self, obj):
        return obj.driver_name
    driver_name.short_description = "Assigned Driver"
