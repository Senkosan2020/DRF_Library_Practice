from django.conf import settings
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, permissions, viewsets, filters, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied

from borrowings.models import Borrowing
from borrowings.serializers import BorrowingReadSerializer
from config.pagination import OptionalLimitOffsetPagination
from .models import Payment
from .serializers import (
    PaymentSerializer,
    PaymentCreateSerializer,
    PaymentReadSerializer,
)
from .throttling import PaymentBurstThrottle, PaymentSustainedThrottle
from decimal import Decimal, InvalidOperation


class PaymentViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """
    /api/payments/           -> list (GET), create (POST)
    /api/payments/<id>/      -> retrieve (GET)
    """

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

    def get_serializer_class(self):
        if self.action == "create":
            return PaymentCreateSerializer
        if self.action in ("list", "retrieve"):
            return PaymentReadSerializer
        return PaymentSerializer

    def get_throttles(self):
        if self.action == "create":
            return [PaymentBurstThrottle(), PaymentSustainedThrottle()]
        return super().get_throttles()

    def create(self, request, *args, **kwargs):
        borrowing_id = request.data.get("borrowing")
        if not borrowing_id:
            return Response(
                {"borrowing": ["This field is required."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        borrowing = get_object_or_404(Borrowing, pk=borrowing_id)

        user = request.user
        if not (user.is_staff or borrowing.user_id == user.id):
            raise PermissionDenied("Forbidden")

        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        payment = serializer.save()
        read_data = PaymentReadSerializer(payment).data
        return Response(read_data, status=status.HTTP_201_CREATED)


class PaymentPreviewView(APIView):
    """
    GET /api/payments/preview/?borrowing=<id>
    """

    permission_classes = [IsAuthenticated]
    throttle_classes = [PaymentBurstThrottle, PaymentSustainedThrottle]

    def get(self, request):
        borrowing_id = request.query_params.get("borrowing")
        if not borrowing_id:
            return Response(
                {"borrowing": ["This query param is required."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        borrowing = get_object_or_404(Borrowing, pk=borrowing_id)

        user = request.user
        if not (user.is_staff or borrowing.user_id == user.id):
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        serialized = BorrowingReadSerializer(borrowing).data  # contains 'late_fee'
        raw_amount = serialized.get("late_fee", "0.00")
        try:
            amount = str(Decimal(str(raw_amount)).quantize(Decimal("0.00")))
        except (InvalidOperation, TypeError):
            amount = "0.00"

        return Response(
            {"borrowing": borrowing.id, "amount": amount},
            status=status.HTTP_200_OK,
        )


class PaymentWebhookView(APIView):
    """
    Stub webhook endpoint:
    - URL: POST /api/payments/webhook/
    - Optional signature check via settings.PAYMENTS_WEBHOOK_SECRET.
    - Always returns 200 for now (no-op), suitable for local/dev.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        # Optional: very simple signature placeholder
        secret = getattr(settings, "PAYMENTS_WEBHOOK_SECRET", None)
        provided = request.headers.get("Stripe-Signature") or request.headers.get(
            "X-Signature"
        )
        if secret and provided != secret:
            return Response(
                {"detail": "Invalid signature"}, status=status.HTTP_400_BAD_REQUEST
            )

        # TODO: parse event and update Payment if needed (future step)
        return Response({"status": "ok"}, status=status.HTTP_200_OK)
