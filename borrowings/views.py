from rest_framework import viewsets, permissions, mixins
from .models import Borrowing
from .serializers import BorrowingReadSerializer, BorrowingCreateSerializer

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
