from rest_framework import viewsets, filters
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
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
class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all().order_by("title", "id")
    serializer_class = BookSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_class = BookFilter
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering_fields = ("title", "author", "inventory", "daily_fee")
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ["title", "author", "daily_fee", "inventory", "id"]
    ordering = ["title"]

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
        return super().create(request, *args, **kwargs)
