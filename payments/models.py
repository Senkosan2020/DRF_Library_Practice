from django.db import models
from django.db.models import Q


class Payment(models.Model):
    TYPE_PAYMENT = "PAYMENT"
    TYPE_FINE = "FINE"
    TYPE_CHOICES = [
        (TYPE_PAYMENT, "Payment"),
        (TYPE_FINE, "Fine"),
    ]

    STATUS_PENDING = "PENDING"
    STATUS_PAID = "PAID"
    STATUS_FAILED = "FAILED"
    STATUS_REFUNDED = "REFUNDED"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PAID, "Paid"),
        (STATUS_FAILED, "Failed"),
        (STATUS_REFUNDED, "Refunded"),
    ]

    borrowing = models.ForeignKey(
        "borrowings.Borrowing",
        on_delete=models.PROTECT,
        related_name="payments",
    )
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    amount = models.DecimalField(max_digits=9, decimal_places=2)

    session_url = models.URLField(blank=True, null=True)
    session_id = models.CharField(max_length=255, blank=True, null=True)

    paid_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                name="payment_amount_positive",
                condition=Q(amount__gt=0),
            ),
        ]
        indexes = [
            models.Index(fields=["borrowing"]),
            models.Index(fields=["status"]),
            models.Index(fields=["type"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return (
            f"{self.type} {self.status} {self.amount} for borrowing {self.borrowing_id}"
        )
