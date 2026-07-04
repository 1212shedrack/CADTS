# billing/serializers.py
from rest_framework import serializers
from .models import Billing


class BillingSerializer(serializers.ModelSerializer):
    """Full billing record with request and user context."""
    request_id = serializers.IntegerField(source='request.id', read_only=True)
    user_name = serializers.SerializerMethodField()
    ambulance_name = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    pickup_latitude = serializers.SerializerMethodField()
    pickup_longitude = serializers.SerializerMethodField()
    destination = serializers.SerializerMethodField()
    trip_date = serializers.SerializerMethodField()

    class Meta:
        model = Billing
        fields = [
            "id",
            "request_id",
            "user_name",
            "ambulance_name",
            "status",
            "pickup_latitude",
            "pickup_longitude",
            "destination",
            "distance_km",
            "base_fee",
            "price_per_km",
            "total_cost",
            "trip_date",
            "created_at",
        ]
        read_only_fields = fields

    def get_user_name(self, obj):
        try:
            return obj.request.user.full_name or obj.request.user.email
        except Exception:
            return "—"

    def get_ambulance_name(self, obj):
        try:
            return obj.request.ambulance.ambulance_name
        except Exception:
            return "—"

    def get_status(self, obj):
        try:
            return obj.request.status
        except Exception:
            return "completed"

    def get_pickup_latitude(self, obj):
        try:
            return float(obj.request.pickup_latitude)
        except Exception:
            return None

    def get_pickup_longitude(self, obj):
        try:
            return float(obj.request.pickup_longitude)
        except Exception:
            return None

    def get_destination(self, obj):
        try:
            return obj.request.destination_hospital or "—"
        except Exception:
            return "—"

    def get_trip_date(self, obj):
        try:
            return obj.request.updated_at.date().isoformat()
        except Exception:
            return None
