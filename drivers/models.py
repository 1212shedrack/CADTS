from django.db import models
from django.conf import settings


class DriverProfile(models.Model):
    """
    Extended profile for drivers — linked 1-to-1 with CustomUser (role=driver).
    License number and driver-specific status are stored here.
    """

    class Status(models.TextChoices):
        ACTIVE = "active",   "Active"
        INACTIVE = "inactive", "Inactive"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="driver_profile"
    )
    license_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=10,
                              choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cadts_driver_profiles"
        verbose_name = "Driver Profile"

    def __str__(self):
        # keep line length within 79 chars to satisfy linters
        return (
            f"Driver: {self.user.full_name} | "
            f"License: {self.license_number}"
        )
