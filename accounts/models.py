# accounts/models.py
# Custom User model with role-based access for CADTS

from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import BaseUserManager, PermissionsMixin
from django.db import models


class CustomUserManager(BaseUserManager):
    """Manager for CustomUser — creates regular users and superusers."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email address is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", CustomUser.Role.ADMIN)
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Central user model for CADTS.
    All actors (User, Driver, Admin) share this model — differentiated by `role`.
    """

    class Role(models.TextChoices):
        USER = "user",   "User"
        DRIVER = "driver", "Driver"
        ADMIN = "admin",  "Admin"

    # Identity
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True)

    # Role
    role = models.CharField(max_length=10, choices=Role.choices,
                            default=Role.USER)

    # Location (updated in real-time for drivers)
    latitude = models.DecimalField(max_digits=9,
                                   decimal_places=6,
                                   null=True, blank=True)
    longitude = models.DecimalField(max_digits=9,
                                    decimal_places=6,
                                    null=True, blank=True)

    # Status flags
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)   # Django admin access
    is_approved = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        db_table = "cadts_users"
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.role})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def is_user_role(self):
        return self.role == self.Role.USER

    @property
    def is_driver_role(self):
        return self.role == self.Role.DRIVER

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN
