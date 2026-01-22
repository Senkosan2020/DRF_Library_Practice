from django.utils import timezone
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, permissions, serializers, status, viewsets, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAdminUser
from datetime import date

from books.models import Book
from .models import Borrowing
from .serializers import BorrowingCreateSerializer, BorrowingReadSerializer

from config.pagination import OptionalLimitOffsetPagination
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiResponse,
    OpenApiExample,
)
from drf_spectacular.types import OpenApiTypes
from .throttling import (
    BorrowingBurstThrottle,
    BorrowingSustainedThrottle,
    ReturnBurstThrottle,
    ReturnSustainedThrottle,
)
from .filters import BorrowingFilter
import csv
import io
from django.http import HttpResponse

@extend_schema_view(
    list=extend_schema(
        tags=["Borrowings"],
        parameters=[
            OpenApiParameter(
                name="is_active",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description="Filter by active status (true/false)."
            ),
            OpenApiParameter(
                name="user_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Filter by user id (admin only)."
            ),
        ],
        responses={200: BorrowingReadSerializer(many=True)},
        description="List borrowings with optional filters."
    ),
    retrieve=extend_schema(
        tags=["Borrowings"],
        responses={200: BorrowingReadSerializer},
        description="Retrieve a borrowing by id."
    ),
    create=extend_schema(
        tags=["Borrowings"],
        request=BorrowingCreateSerializer,
        responses={201: BorrowingReadSerializer},
        description="Create a new borrowing."
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
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = BorrowingFilter
    ordering_fields = ["borrow_date", "expected_return_date", "actual_return_date", "id"]
    ordering = ["-borrow_date"]

    queryset = Borrowing.objects.select_related("book", "user").order_by("-borrow_date", "-id")

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="is_active",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description="Filter active borrowings (true/false, 1/0)",
            ),
            OpenApiParameter(
                name="user_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Admin only: filter by user id",
            ),
        ],
        responses={200: BorrowingReadSerializer},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

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

    @extend_schema(
        responses={
            200: BorrowingReadSerializer,
            403: OpenApiResponse(description="Forbidden"),
            404: OpenApiResponse(description="Not found"),
            429: OpenApiResponse(description="Throttled"),
        },
        examples=[
            OpenApiExample(
                "Return borrowing",
                description="Mark borrowing as returned",
                value=None,
            ),
        ],
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="return",
        throttle_classes=[ReturnBurstThrottle, ReturnSustainedThrottle],
    )
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

    @extend_schema(
        tags=["Borrowings"],
        summary="Borrowings stats",
        description="Aggregated counters for the current user (or all users for admin).",
        responses={200: OpenApiTypes.OBJECT},
    )
    @action(detail=False, methods=["get"], url_path="stats")
    def stats(self, request):
        qs = self.get_queryset()
        today = timezone.localdate()

        total = qs.count()
        active = qs.filter(actual_return_date__isnull=True).count()
        returned = total - active
        overdue_active = qs.filter(
            actual_return_date__isnull=True, expected_return_date__lt=today
        ).count()

        data = {
            "total": total,
            "active": active,
            "returned": returned,
            "overdue_active": overdue_active,
        }
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="export")
    def export(self, request):
        # respect filters/order/pagination inputs but export full filtered set
        qs = self.filter_queryset(self.get_queryset())

        output = io.StringIO()
        writer = csv.writer(output)

        is_admin = request.user.is_staff
        headers = ["id", "book", "borrow_date", "expected_return_date", "actual_return_date", "is_overdue"]
        if is_admin:
            headers.insert(1, "user_email")
        writer.writerow(headers)

        today = timezone.localdate()
        for b in qs:
            row = [b.id]
            if is_admin:
                row.append(b.user.email)
            row.extend([
                b.book.title,
                b.borrow_date.isoformat(),
                b.expected_return_date.isoformat(),
                b.actual_return_date.isoformat() if b.actual_return_date else "",
                int(b.actual_return_date is None and b.expected_return_date < today),
            ])
            writer.writerow(row)

        content = output.getvalue()
        output.close()

        response = HttpResponse(content, content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="borrowings.csv"'
        return response
