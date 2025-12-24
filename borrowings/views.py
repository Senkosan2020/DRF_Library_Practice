from rest_framework import viewsets, permissions, mixins, serializers, status
from rest_framework.response import Response
from rest_framework.decorators import action
from books.models import Book
from .models import Borrowing
from .serializers import BorrowingReadSerializer, BorrowingCreateSerializer
from django.db import transaction
from django.utils import timezone

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

    @action(detail=True, methods=["post"], url_path="return")
    @transaction.atomic
    def return_borrowing(self, request, pk=None):
        borrowing = self.get_object()
        if not request.user.is_staff and borrowing.user_id != request.user.id:
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        if borrowing.actual_return_date is not None:
            return Response({"detail": "Already returned"}, status=status.HTTP_400_BAD_REQUEST)

        book = Book.objects.select_for_update().get(pk=borrowing.book_id)
        book.inventory += 1
        book.save(update_fields=["inventory"])

        borrowing.actual_return_date = timezone.now().date()
        borrowing.save(update_fields=["actual_return_date"])

        data = BorrowingReadSerializer(borrowing).data
        return Response(data, status=status.HTTP_200_OK)
