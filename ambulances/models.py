# ambulances/models.py
# Ambulance model for CADTS

from django.db import models
from django.conf import settings


class Ambulance(models.Model):
    """
    Represents a registered ambulance in the CADTS system.
    - Admin registers and assigns a driver.
    - Status changes as requests are processed.
    - Location is updated in real-time by the driver.
    """

    class Status(models.TextChoices):
        AVAILABLE   = "available",    "Available"
        BUSY        = "busy",         "Busy"
        OFFLINE     = "offline",      "Offline"
        MAINTENANCE = "maintenance",  "Maintenance"

    plate_number   = models.CharField(max_length=20, unique=True)
    ambulance_name = models.CharField(max_length=100)

    driver         = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="ambulance",
        limit_choices_to={"role": "driver"},
    )

    latitude       = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude      = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    status         = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.OFFLINE,
    )

    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        db_table     = "cadts_ambulances"
        verbose_name = "Ambulance"
        ordering     = ["-created_at"]

    def __str__(self):
        return f"{self.ambulance_name} ({self.plate_number}) — {self.status}"

    @property
    def driver_name(self):
        return self.driver.full_name if self.driver else "Unassigned"

    @property
    def is_available(self):
        return self.status == self.Status.AVAILABLE
