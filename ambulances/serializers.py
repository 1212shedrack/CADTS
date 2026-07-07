# ambulances/serializers.py
from rest_framework import serializers
from .models import Ambulance
from accounts.models import CustomUser


class DriverChoiceSerializer(serializers.ModelSerializer):
    """Light serializer for listing available drivers in dropdown."""

    class Meta:
        model = CustomUser
        fields = ["id", "full_name", "email"]


class AmbulanceSerializer(serializers.ModelSerializer):
    driver_name = serializers.SerializerMethodField()
    driver_info = DriverChoiceSerializer(source='driver', read_only=True)

    class Meta:
        model = Ambulance
        fields = [
            "id", "plate_number", "ambulance_name",
            "driver", "driver_name", "driver_info",
            "latitude", "longitude",
            "status", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_driver_name(self, obj):
        """Return driver's full name or 'Unassigned'."""
        return obj.driver.full_name if obj.driver else "Unassigned"

    def validate_driver(self, value):
        """Ensure a driver is not assigned to two ambulances."""
        if value:
            qs = Ambulance.objects.filter(driver=value)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    "This driver is already assigned to another ambulance."
                )
        return value


class AmbulanceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ambulance
        fields = ["plate_number", "ambulance_name", "driver", "status"]

    def validate_driver(self, value):
        if value:
            qs = Ambulance.objects.filter(driver=value)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    "This driver is already assigned to another ambulance."
                )
        return value
