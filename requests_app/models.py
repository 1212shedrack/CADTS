from django.db import models
from django.conf import settings


class Request(models.Model):
    """
    Represents a citizen's ambulance request.
    Tracks full lifecycle: Pending → Accepted → Busy → Completed.
    Full implementation: Phase 6
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"
        ARRIVED = "arrived",  "Arrived"
        PATIENT_PICKED = "patient_picked", "Patient Picked"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="requests",
        limit_choices_to={"role": "user"},
    )
    ambulance = models.ForeignKey(
        "ambulances.Ambulance",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="requests",
    )
    pickup_latitude = models.DecimalField(max_digits=20,
                                          decimal_places=10,
                                          null=True, blank=True)
    pickup_longitude = models.DecimalField(max_digits=20,
                                           decimal_places=10,
                                           null=True, blank=True)
    destination_hospital = models.CharField(max_length=255,
                                            blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cadts_requests"
        verbose_name = "Ambulance Request"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Request #{self.pk} by {self.user.full_name} — {self.status}"

    @property
    def user_name(self):
        return self.user.full_name if self.user else "—"

    @property
    def ambulance_name(self):
        return self.ambulance.ambulance_name if self.ambulance else "—"

    @property
    def total_cost(self):
        try:
            return self.billing.total_cost
        except Exception:
            return None

    @property
    def distance(self):
        try:
            return self.billing.distance_km
        except Exception:
            return None
