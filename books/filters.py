import django_filters
from .models import Book

class BookFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(field_name="title", lookup_expr="icontains")
    author = django_filters.CharFilter(field_name="author", lookup_expr="icontains")
    cover = django_filters.CharFilter(field_name="cover")  # exact HARD/SOFT

    # NEW: return only books with inventory > 0 when true
    available_only = django_filters.BooleanFilter(method="filter_available_only")

    class Meta:
        model = Book
        fields = ("title", "author", "cover", "available_only")

    def filter_available_only(self, queryset, name, value):
        if value:
            return queryset.filter(inventory__gt=0)
        return queryset
