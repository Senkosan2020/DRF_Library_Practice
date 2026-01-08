from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import PaymentViewSet, PaymentPreviewView, PaymentCreateView

router = DefaultRouter()
router.register("payments", PaymentViewSet, basename="payment")

urlpatterns = [
    path("", include(router.urls)),  # /api/payments/, /api/payments/<id>/
    path(
        "payments/preview/", PaymentPreviewView.as_view(), name="payments-preview"
    ),  # /api/payments/preview/
    path(
        "payments/create/", PaymentCreateView.as_view(), name="payments-create"
    ),  # /api/payments/create/
]
