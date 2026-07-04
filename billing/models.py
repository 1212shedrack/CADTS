from django.db import models
# from django.conf import settings


class Billing(models.Model):
    """
    Stores billing records for completed ambulance trips.
    Formula: total_cost = base_fee + (distance_km × price_per_km)
    Full implementation: Phase 8
    """
    request = models.OneToOneField(
        "requests_app.Request",
        on_delete=models.CASCADE,
        related_name="billing",
        null=True, blank=True,
    )
    distance_km = models.DecimalField(max_digits=8,
                                      decimal_places=3,
                                      default=0)
    base_fee = models.DecimalField(max_digits=10,
                                   decimal_places=2,
                                   default=5000)
    price_per_km = models.DecimalField(max_digits=8,
                                       decimal_places=2,
                                       default=2000)
    total_cost = models.DecimalField(max_digits=12,
                                     decimal_places=2,
                                     default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cadts_billing"
        verbose_name = "Billing Record"

    def __str__(self):
        return f"Bill #{self.pk} — Tsh {self.total_cost}"

    def calculate(self):
        """Compute and save the total cost."""
        self.total_cost = (
            self.base_fee + (self.distance_km * self.price_per_km)
        )
        self.save()
