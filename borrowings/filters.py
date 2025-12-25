import django_filters
from borrowings.models import Borrowing


class BorrowingFilter(django_filters.FilterSet):
    # ?is_active=true/false — filter by open/returned borrowings
    is_active = django_filters.BooleanFilter(method="filter_is_active")
    # ?user_id=... — works only for staff; ignored for regular users
    user_id = django_filters.NumberFilter(method="filter_user_id")

    class Meta:
        model = Borrowing
        fields = ["is_active", "user_id", "book"]

    def filter_is_active(self, queryset, name, value):
        if value is True:
            return queryset.filter(actual_return_date__isnull=True)
        if value is False:
            return queryset.filter(actual_return_date__isnull=False)
        return queryset

    def filter_user_id(self, queryset, name, value):
        user = getattr(self.request, "user", None)
        if user and user.is_staff:
            return queryset.filter(user_id=value)
        # Non-staff: ignore the param; viewset already limits to own records
        return queryset
