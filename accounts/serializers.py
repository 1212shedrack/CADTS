# accounts/serializers.py
# Registration and Authentication serializers for CADTS

from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CustomUser


# ─────────────────────────────────────────────────────────────────────────────
# USER REGISTRATION
# ─────────────────────────────────────────────────────────────────────────────
class UserRegisterSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only=True, min_length=6)
    password2 = serializers.CharField(write_only=True, label="Confirm Password")

    class Meta:
        model  = CustomUser
        fields = ["first_name", "last_name", "email", "phone", "password", "password2"]

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        user = CustomUser.objects.create_user(
            role=CustomUser.Role.USER,
            **validated_data
        )
        return user


# ─────────────────────────────────────────────────────────────────────────────
# DRIVER REGISTRATION
# ─────────────────────────────────────────────────────────────────────────────
class DriverRegisterSerializer(serializers.ModelSerializer):
    password       = serializers.CharField(write_only=True, min_length=6)
    password2      = serializers.CharField(write_only=True, label="Confirm Password")
    license_number = serializers.CharField(max_length=50)

    class Meta:
        model  = CustomUser
        fields = ["first_name", "last_name", "email", "phone", "license_number", "password", "password2"]

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        license_number = validated_data.pop("license_number")

        user = CustomUser.objects.create_user(
            role=CustomUser.Role.DRIVER,
            is_approved=False,   # Drivers must be approved by admin
            **validated_data
        )
        # Save license number in DriverProfile
        from drivers.models import DriverProfile
        DriverProfile.objects.create(user=user, license_number=license_number)
        return user


# ─────────────────────────────────────────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────────────────────────────────────────
class LoginSerializer(serializers.Serializer):
    email    = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(username=attrs["email"], password=attrs["password"])
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("Your account has been deactivated.")
        if user.is_driver_role and not user.is_approved:
            raise serializers.ValidationError("Your driver account is pending admin approval.")
        attrs["user"] = user
        return attrs


# ─────────────────────────────────────────────────────────────────────────────
# USER PROFILE
# ─────────────────────────────────────────────────────────────────────────────
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = CustomUser
        fields = ["id", "first_name", "last_name", "email", "phone", "role",
                  "latitude", "longitude", "is_approved", "created_at"]
        read_only_fields = ["id", "email", "role", "created_at"]
