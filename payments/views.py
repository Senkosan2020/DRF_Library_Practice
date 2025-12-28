from decimal import Decimal

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


class PaymentCreateView(APIView):
    """
    POST /api/payments/
    Body: {"borrowing": <id>}
    Creates a Payment linked to the borrowing.
    Amount is derived from borrowing's late_fee
    when the Payment model has an 'amount' field.
    Status is set to PENDING when the model
    defines it (constant or field).
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        borrowing_id = request.data.get("borrowing") or request.data.get("borrowing_id")
        if not borrowing_id:
            return Response(
                {"borrowing": ["This field is required."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        borrowing = get_object_or_404(Borrowing, pk=borrowing_id)

        # Only owner or admin can create a payment for this borrowing
        user = request.user
        if not (user.is_staff or borrowing.user_id == user.id):
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        # Prevent duplicate open payments for the same borrowing
        existing_qs = Payment.objects.filter(borrowing=borrowing)
        if hasattr(Payment, "status"):
            # If the model has a 'status' field, consider PENDING as open
            pending_value = getattr(Payment, "PENDING", "PENDING")
            existing_qs = existing_qs.filter(status=pending_value)
        if existing_qs.exists():
            return Response(
                {"detail": "An open payment already exists for this borrowing."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Compute amount from borrowing serializer (late_fee) if present
        serialized = BorrowingReadSerializer(borrowing).data
        amount = serialized.get("late_fee", "0.00")
        try:
            amount = Decimal(str(amount))
        except Exception:
            amount = Decimal("0.00")

        payment = Payment(borrowing=borrowing)
        if hasattr(payment, "amount"):
            payment.amount = amount
        if hasattr(payment, "status"):
            payment.status = getattr(Payment, "PENDING", "PENDING")
        # Set owner if the model has such a field
        if hasattr(payment, "user"):
            payment.user = user

        payment.save()

        # Build safe response without assuming exact model fields
        payload = {
            "id": payment.pk,
            "borrowing": borrowing.id,
        }
        if hasattr(payment, "amount"):
            payload["amount"] = str(payment.amount)
        if hasattr(payment, "status"):
            payload["status"] = payment.status

        return Response(payload, status=status.HTTP_201_CREATED)
