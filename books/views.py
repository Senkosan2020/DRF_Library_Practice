import csv
import io
from django.http import HttpResponse
from rest_framework import viewsets, filters, permissions, status
from rest_framework.filters import OrderingFilter
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response

from .models import Book
from .serializers import BookSerializer
from .permissions import IsAdminOrReadOnly
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiTypes,
    OpenApiResponse,
    OpenApiExample,
)
from .filters import BookFilter

@extend_schema_view(
    list=extend_schema(
        summary="List books",
        description="Public list of books.",
        parameters=[
            OpenApiParameter(
                name="author",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by author (if supported).",
            ),
            OpenApiParameter(
                name="title",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by title (if supported).",
            ),
            OpenApiParameter(
                name="cover",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Cover type (HARD/SOFT), if supported.",
            ),
        ],
        responses={200: BookSerializer(many=True)},
    ),
    create=extend_schema(
        summary="Create a book",
        description="Create a book (staff only).",
        request=BookSerializer,
        responses={201: BookSerializer},
    ),
)
class BookViewSet(
    viewsets.ModelViewSet
):
    queryset = Book.objects.all().order_by("title", "id")
    serializer_class = BookSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_class = BookFilter
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "author"]
    ordering_fields = ["title", "author", "daily_fee", "inventory", "id"]
    ordering = ["title"]
    http_method_names = ["get", "post"]

    def get_permissions(self):
        # Only admins can create; listing/retrieving is public
        if self.action == "create":
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    @extend_schema(
        summary="List books",
        description="Public endpoint. Supports pagination.",
        responses={200: OpenApiResponse(description="Books list")},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Create a book",
        description="Admin only.",
        responses={
            201: OpenApiResponse(description="Book created"),
            400: OpenApiResponse(description="Validation error"),
            403: OpenApiResponse(description="Forbidden"),
        },
        examples=[
            OpenApiExample(
                "Create book",
                value={
                    "title": "The Pragmatic Programmer",
                    "author": "Andrew Hunt, David Thomas",
                    "cover": "HARD",
                    "inventory": 5,
                    "daily_fee": "1.50",
                },
            )
        ],
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=False, methods=["get"], url_path="export")
    def export(self, request):
        # apply existing filters / ordering
        qs = self.filter_queryset(self.get_queryset())

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(["id", "title", "author", "cover", "inventory", "daily_fee"])
        for b in qs:
            writer.writerow([b.id, b.title, b.author, b.cover, b.inventory, str(b.daily_fee)])

        content = output.getvalue()
        output.close()

        response = HttpResponse(content, content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="books.csv"'
        return response
