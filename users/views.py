from django.contrib.auth import get_user_model
from rest_framework import generics, permissions
from .serializers import RegisterSerializer, MeSerializer
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiTypes
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

User = get_user_model()

@extend_schema(
    summary="Obtain JWT access & refresh tokens",
    description="Authenticate with email & password to receive JWT tokens.",
    request=OpenApiTypes.OBJECT,
    examples=[
        {"request": {"email": "user@example.com", "password": "secret"}},
    ],
    responses={
        200: OpenApiTypes.OBJECT,   # {"access": "<jwt>", "refresh": "<jwt>"}
        401: OpenApiResponse(description="Invalid credentials"),
    },
    tags=["Auth"],
)
class TokenObtainPairDocView(TokenObtainPairView):
    pass


@extend_schema(
    summary="Refresh JWT access token",
    description="Use a valid refresh token to obtain a new access token.",
    request=OpenApiTypes.OBJECT,
    examples=[
        {"request": {"refresh": "<refresh_jwt_token>" }},
    ],
    responses={
        200: OpenApiTypes.OBJECT,   # {"access": "<jwt>"}
        401: OpenApiResponse(description="Invalid or expired refresh token"),
    },
    tags=["Auth"],
)
class TokenRefreshDocView(TokenRefreshView):
    pass

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = MeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
