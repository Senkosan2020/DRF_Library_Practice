from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import PaymentViewSet, PaymentPreviewView

router = DefaultRouter()
router.register(
    "", PaymentViewSet, basename="payment"
)  # CHANGED: keep base at /api/payments/

urlpatterns = [
    path(
        "preview/", PaymentPreviewView.as_view(), name="payments-preview"
    ),  # CHANGED: /api/payments/preview/
    path("", include(router.urls)),  # /api/payments/ , /api/payments/<id>/
]
