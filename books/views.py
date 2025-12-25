from rest_framework import viewsets
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

@extend_schema_view(
    list=extend_schema(
        summary="List books",
        description="Публічний список книжок.",
        parameters=[
            OpenApiParameter(
                name="author",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Фільтр за автором (якщо підтримується у фільтрах).",
            ),
            OpenApiParameter(
                name="title",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Фільтр за назвою (якщо підтримується).",
            ),
            OpenApiParameter(
                name="cover",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Тип обкладинки (HARD/SOFT), якщо підтримується.",
            ),
        ],
        responses={200: BookSerializer(many=True)},
    ),
    create=extend_schema(
        summary="Create a book",
        description="Створення книжки (тільки staff).",
        request=BookSerializer,
        responses={201: BookSerializer},
    ),
)
class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all().order_by("title", "id")
    serializer_class = BookSerializer
    permission_classes = [IsAdminOrReadOnly]

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
