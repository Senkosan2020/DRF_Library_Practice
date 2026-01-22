from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import TokenObtainPairDocView, TokenRefreshDocView,RegisterView, MeView

urlpatterns = [
    path("", RegisterView.as_view(), name="users-register"),
    path("me/", MeView.as_view(), name="users-me"),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/", TokenObtainPairDocView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshDocView.as_view(), name="token_refresh"),
]
