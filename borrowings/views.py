from rest_framework import viewsets, permissions, mixins, serializers, status
from rest_framework.response import Response
from books.models import Book
from .models import Borrowing
from .serializers import BorrowingReadSerializer, BorrowingCreateSerializer
from django.db import transaction

class BorrowingViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = BorrowingReadSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post"]  # забороняємо put/patch/delete

    def get_queryset(self):
        qs = Borrowing.objects.select_related("book", "user").order_by("-id")
        return qs if self.request.user.is_staff else qs.filter(user=self.request.user)

    def get_serializer_class(self):
        return BorrowingCreateSerializer if self.action == "create" else BorrowingReadSerializer

    @transaction.atomic
    def perform_create(self, serializer):
        book = serializer.validated_data["book"]
        locked_book = Book.objects.select_for_update().get(pk=book.pk)
        if locked_book.inventory <= 0:
            raise serializers.ValidationError({"book": "No inventory available"})
        locked_book.inventory -= 1
        locked_book.save(update_fields=["inventory"])
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        create_serializer = self.get_serializer(data=request.data)
        create_serializer.is_valid(raise_exception=True)
        self.perform_create(create_serializer)
        instance = create_serializer.instance
        read_data = BorrowingReadSerializer(instance).data
        headers = self.get_success_headers(read_data)
        return Response(read_data, status=status.HTTP_201_CREATED, headers=headers)
