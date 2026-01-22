from django.conf import settings
from django.db import models
from django.db.models import Q, F

class Borrowing(models.Model):
    borrow_date = models.DateField()
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)

    book = models.ForeignKey("books.Book", on_delete=models.PROTECT, related_name="borrowings")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="borrowings")

    class Meta:
        constraints = [
            models.CheckConstraint(
                name="borrow_expected_gte_borrow",
                check=Q(expected_return_date__gte=F("borrow_date")),
            ),
            models.CheckConstraint(
                name="borrow_actual_null_or_gte_borrow",
                check=Q(actual_return_date__isnull=True) | Q(actual_return_date__gte=F("borrow_date")),
            ),
        ]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["actual_return_date"]),
            models.Index(fields=["expected_return_date"]),
            models.Index(fields=["user", "actual_return_date"]),
            models.Index(fields=["actual_return_date", "expected_return_date"]),
        ]

    def __str__(self):
        return f"{self.user_id} → {self.book_id} [{self.borrow_date}..{self.expected_return_date}]"

    @property
    def is_active(self) -> bool:
        return self.actual_return_date is None
