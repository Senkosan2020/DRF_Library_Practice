from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, permissions, viewsets, filters

from config.pagination import OptionalLimitOffsetPagination
from .models import Payment
from .serializers import PaymentSerializer


class PaymentViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = OptionalLimitOffsetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["borrowing", "status", "type"]
    ordering_fields = ["created_at", "amount", "paid_at", "id"]
    ordering = ["-created_at"]

    queryset = (
        Payment.objects.select_related(
            "borrowing", "borrowing__book", "borrowing__user"
        )
        .all()
        .order_by("-created_at", "-id")
    )

    def get_queryset(self):
        qs = self.queryset
        user = self.request.user
        if not user.is_staff:
            qs = qs.filter(borrowing__user=user)
        return qs
