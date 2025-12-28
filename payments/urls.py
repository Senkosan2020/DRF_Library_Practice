from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import PaymentViewSet, PaymentPreviewView

router = DefaultRouter()
router.register("payments", PaymentViewSet, basename="payment")

urlpatterns = [
    path("", include(router.urls)),
    path("preview/", PaymentPreviewView.as_view(), name="payments-preview"),
]
