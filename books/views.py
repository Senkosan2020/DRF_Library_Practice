from rest_framework import viewsets
from .models import Book
from .serializers import BookSerializer
from .permissions import IsAdminOrReadOnly
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

@extend_schema(tags=["Books"])
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
