from django.urls import path
from .views import BorrowingViewSet

borrowing_list = BorrowingViewSet.as_view({
    "get": "list",
    "post": "create",
})

borrowing_detail = BorrowingViewSet.as_view({
    "get": "retrieve",
})

borrowing_return = BorrowingViewSet.as_view({
    "post": "return_borrowing",
})

borrowing_overdue = BorrowingViewSet.as_view({
    "get": "overdue",
})

urlpatterns = [
    # /api/borrowings/
    path("", borrowing_list, name="borrowing-list"),
    # /api/borrowings/<id>/
    path("<int:pk>/", borrowing_detail, name="borrowing-detail"),
    # /api/borrowings/<id>/return/
    path("<int:pk>/return/", borrowing_return, name="borrowing-return"),
    # /api/borrowings/overdue/
    path("overdue/", borrowing_overdue, name="borrowing-overdue"),
]
