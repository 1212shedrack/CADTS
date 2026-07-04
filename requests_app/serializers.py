# requests_app/serializers.py
from rest_framework import serializers
from .models import Request
from ambulances.models import Ambulance


class RequestCreateSerializer(serializers.ModelSerializer):
    """User creates a new ambulance request."""
    class Meta:
        model = Request
        fields = ["ambulance", "pickup_latitude", "pickup_longitude",
                  "destination_hospital", "notes"]

    def validate_ambulance(self, ambulance):
        if ambulance and ambulance.status != Ambulance.Status.AVAILABLE:
            raise serializers.ValidationError(
                "This ambulance is not available. Please choose another."
            )
        return ambulance

    def validate(self, attrs):
        user = self.context["request"].user
        active = Request.objects.filter(
            user=user,
            status__in=[
                Request.Status.PENDING,
                Request.Status.ACCEPTED,
                Request.Status.ARRIVED,
                Request.Status.PATIENT_PICKED,
            ]
        ).exists()
        if active:
            raise serializers.ValidationError(
                "You already have an active request."
                "Cancel it before making a new one."
            )
        return attrs

    def create(self, validated_data):
        user = self.context["request"].user
        ambulance = validated_data.get("ambulance")
        request = Request.objects.create(user=user, **validated_data)
        # Mark ambulance as busy while pending
        if ambulance:
            ambulance.status = Ambulance.Status.BUSY
            ambulance.save()
            # Push real-time notification to driver via WebSocket
            if ambulance.driver:
                try:
                    from channels.layers import get_channel_layer
                    from asgiref.sync import async_to_sync
                    channel_layer = get_channel_layer()
                    group_name = f"driver_{ambulance.driver.pk}_notifications"
                    async_to_sync(channel_layer.group_send)(
                        group_name,
                        {
                            "type":       "new_request",
                            "request_id": request.pk,
                            "user_name":  user.full_name or user.email,
                            "user_id":    user.pk,
                            "message": (
                                f"New request from {user.full_name or user.email}!"
                            ),
                        }
                    )
                except Exception:
                    pass  # Channel layer unavailable — degrade gracefully
        return request


class RequestSerializer(serializers.ModelSerializer):
    """Full request detail — includes user/ambulance info and billing."""
    user_name = serializers.SerializerMethodField()
    ambulance_name = serializers.SerializerMethodField()
    ambulance_latitude = serializers.SerializerMethodField()
    ambulance_longitude = serializers.SerializerMethodField()
    total_cost = serializers.SerializerMethodField()
    distance = serializers.SerializerMethodField()

    class Meta:
        model  = Request
        fields = [
            "id", "user", "user_name",
            "ambulance", "ambulance_name",
            "ambulance_latitude", "ambulance_longitude",
            "pickup_latitude", "pickup_longitude",
            "destination_hospital", "status", "notes",
            "total_cost", "distance",
            "created_at", "updated_at",
        ]

    def get_user_name(self, obj):
        return obj.user.full_name if obj.user else "—"

    def get_ambulance_name(self, obj):
        return obj.ambulance.ambulance_name if obj.ambulance else "—"

    def get_ambulance_latitude(self, obj):
        return float(obj.ambulance.latitude) if (obj.ambulance and obj.ambulance.latitude) else None

    def get_ambulance_longitude(self, obj):
        return float(obj.ambulance.longitude) if (obj.ambulance and obj.ambulance.longitude) else None

    def get_total_cost(self, obj):
        try:
            return float(obj.billing.total_cost)
        except Exception:
            return None

    def get_distance(self, obj):
        try:
            return float(obj.billing.distance_km)
        except Exception:
            return None
