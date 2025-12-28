from rest_framework.pagination import LimitOffsetPagination


class OptionalLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 10

    def paginate_queryset(self, queryset, request, view=None):
        if not request.query_params.get("limit") and not request.query_params.get(
            "offset"
        ):
            return None
        return super().paginate_queryset(queryset, request, view)
