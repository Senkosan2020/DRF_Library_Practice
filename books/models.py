from django.db import models
from django.db.models import Q


class Book(models.Model):
    HARD = "HARD"
    SOFT = "SOFT"
    COVER_CHOICES = [
        (HARD, "Hard"),
        (SOFT, "Soft"),
    ]

    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    cover = models.CharField(max_length=4, choices=COVER_CHOICES)
    inventory = models.PositiveIntegerField()
    daily_fee = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.title} — {self.author}"

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(inventory__gte=0),
                name="book_inventory_non_negative",
            ),
            models.CheckConstraint(
                check=Q(daily_fee__gt=0),
                name="book_daily_fee_positive",
            ),
        ]
        indexes = [
            models.Index(fields=["title"]),
            models.Index(fields=["author"]),
            models.Index(fields=["cover"]),
            models.Index(fields=["title", "author"]),
        ]
