from django.utils import timezone
from django.db import transaction
from rest_framework import mixins, permissions, serializers, status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action

from books.models import Book
from .models import Borrowing
from .serializers import BorrowingCreateSerializer, BorrowingReadSerializer

from config.pagination import OptionalLimitOffsetPagination
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiTypes

@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(name="is_active", type=OpenApiTypes.STR, description="true|false"),
            OpenApiParameter(name="user_id", type=OpenApiTypes.INT, description="Admin only"),
            OpenApiParameter(name="overdue", type=OpenApiTypes.STR, description="true|false"),
            OpenApiParameter(name="limit", type=OpenApiTypes.INT, description="Enable pagination"),
            OpenApiParameter(name="offset", type=OpenApiTypes.INT, description="Pagination offset"),
        ]
    ),
)
class BorrowingViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post"]
    pagination_class = OptionalLimitOffsetPagination

    queryset = Borrowing.objects.select_related("book", "user").order_by("-id")

    def get_queryset(self):
        qs = self.queryset
        u = self.request.user

        if not u.is_staff:
            qs = qs.filter(user=u)

        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            v = is_active.lower()
            if v == "true":
                qs = qs.filter(actual_return_date__isnull=True)
            elif v == "false":
                qs = qs.filter(actual_return_date__isnull=False)

        user_id = self.request.query_params.get("user_id")
        if user_id and u.is_staff:
            qs = qs.filter(user_id=user_id)

        overdue = self.request.query_params.get("overdue")
        if overdue is not None:
            today = timezone.localdate()
            v = overdue.lower()
            if v == "true":
                qs = qs.filter(actual_return_date__isnull=True, expected_return_date__lt=today)
            elif v == "false":
                qs = qs.exclude(actual_return_date__isnull=True, expected_return_date__lt=today)

        return qs

    def get_serializer_class(self):
        return BorrowingCreateSerializer if self.action == "create" else BorrowingReadSerializer

    @transaction.atomic
    def perform_create(self, serializer):
        book = serializer.validated_data["book"]
        b = Book.objects.select_for_update().get(pk=book.pk)
        if b.inventory <= 0:
            raise serializers.ValidationError({"book": "No inventory available"})
        b.inventory -= 1
        b.save(update_fields=["inventory"])
        serializer.save(user=self.request.user)

    @extend_schema(operation_id="borrowing_return",
                       description="Return a borrowing, increment inventory, set actual_return_date")
    @action(detail=True, methods=["post"], url_path="return")
    @transaction.atomic
    def return_borrowing(self, request, pk=None):
        try:
            borrowing = Borrowing.objects.select_related("book", "user").get(pk=pk)
        except Borrowing.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        if not request.user.is_staff and borrowing.user_id != request.user.id:
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        if borrowing.actual_return_date is not None:
            return Response({"detail": "Already returned"}, status=status.HTTP_400_BAD_REQUEST)

        book = Book.objects.select_for_update().get(pk=borrowing.book_id)
        book.inventory += 1
        book.save(update_fields=["inventory"])

        actual = max(timezone.localdate(), borrowing.borrow_date)
        borrowing.actual_return_date = actual
        borrowing.save(update_fields=["actual_return_date"])

        return Response(BorrowingReadSerializer(borrowing).data, status=status.HTTP_200_OK)
