from django.utils import timezone
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from rest_framework import mixins, permissions, serializers, status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAdminUser
from datetime import date

from books.models import Book
from .models import Borrowing
from .serializers import BorrowingCreateSerializer, BorrowingReadSerializer

from config.pagination import OptionalLimitOffsetPagination
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiTypes
from .throttling import (
    BorrowingBurstThrottle,
    BorrowingSustainedThrottle,
    ReturnBurstThrottle,
    ReturnSustainedThrottle,
)

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
        vd = serializer.validated_data
        if isinstance(vd, list):
            if len(vd) != 1:
                raise serializers.ValidationError({"non_field_errors": ["Bulk create is not supported."]})
            vd = vd[0]

        book = vd["book"]
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
        borrowing = get_object_or_404(Borrowing, pk=pk)

        if not (request.user.is_staff or borrowing.user_id == request.user.id):
            raise PermissionDenied("You cannot return someone else's borrowing")

        if borrowing.actual_return_date is not None:
            return Response(
                {"detail": "Already returned"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Повернення сьогодні + інвентар +1
        borrowing.actual_return_date = date.today()
        borrowing.save(update_fields=["actual_return_date"])

        Book.objects.filter(pk=borrowing.book_id).update(inventory=F("inventory") + 1)

        data = BorrowingReadSerializer(borrowing).data
        return Response(data, status=status.HTTP_200_OK)

    def get_throttles(self):
        if self.action == "create":
            return [BorrowingBurstThrottle(), BorrowingSustainedThrottle()]
        if self.action == "return_borrowing":
            return [ReturnBurstThrottle(), ReturnSustainedThrottle()]
        return []

    @action(detail=False, methods=["get"], url_path="overdue", permission_classes=[IsAdminUser])
    def overdue(self, request):
        today = timezone.localdate()
        qs = self.get_queryset().filter(
            actual_return_date__isnull=True,
            expected_return_date__lt=today,
        )
        page = self.paginate_queryset(qs)
        if page is not None:
            ser = BorrowingReadSerializer(page, many=True)
            return self.get_paginated_response(ser.data)

        ser = BorrowingReadSerializer(qs, many=True)
        return Response(ser.data)
