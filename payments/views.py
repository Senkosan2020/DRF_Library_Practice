from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, permissions, viewsets, filters, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from borrowings.models import Borrowing
from borrowings.serializers import BorrowingReadSerializer
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


class PaymentPreviewView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        borrowing_id = request.data.get("borrowing") or request.data.get("borrowing_id")
        if not borrowing_id:
            return Response(
                {"borrowing": ["This field is required."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        borrowing = get_object_or_404(Borrowing, pk=borrowing_id)

        user = request.user
        if not (user.is_staff or borrowing.user_id == user.id):
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        # Reuse existing read-serializer to get computed late_fee if present
        serialized = BorrowingReadSerializer(borrowing).data
        amount = serialized.get("late_fee", "0.00")

        return Response(
            {"borrowing": borrowing.id, "amount": amount},
            status=status.HTTP_200_OK,
        )
