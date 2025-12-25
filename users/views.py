from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, serializers
from .serializers import RegisterSerializer, MeSerializer
from drf_spectacular.utils import OpenApiTypes, extend_schema, extend_schema_view, inline_serializer, OpenApiExample, OpenApiResponse
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

@extend_schema_view(
    post=extend_schema(
        tags=["Users"],
        summary="Register a new user",
        description="Create an account using email and password.",
        request=inline_serializer(
            name="RegisterRequest",
            fields={
                "email": serializers.EmailField(),
                "password": serializers.CharField(write_only=True)
            }
        ),
        responses={
            201: inline_serializer(
                name="RegisterResponse",
                fields={
                    "id": serializers.IntegerField(),
                    "email": serializers.EmailField()
                }
            ),
            400: OpenApiResponse(description="Validation error"),
        },
        examples=[
            OpenApiExample(
                "Valid payload",
                value={"email": "user@example.com", "password": "strong-pass"},
            )
        ],
    )
)
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

@extend_schema_view(
    get=extend_schema(
        tags=["Users"],
        summary="Get current user profile",
        responses={
            200: inline_serializer(
                name="MeResponse",
                fields={
                    "id": serializers.IntegerField(),
                    "email": serializers.EmailField(),
                    "is_staff": serializers.BooleanField()
                }
            )
        }
    ),
    patch=extend_schema(
        tags=["Users"],
        summary="Update current user profile",
        description="Update allowed fields of the current user. Password, if accepted here, is write-only.",
        request=inline_serializer(
            name="MeUpdateRequest",
            fields={
                "password": serializers.CharField(required=False, write_only=True)
            }
        ),
        responses={
            200: inline_serializer(
                name="MeUpdateResponse",
                fields={
                    "id": serializers.IntegerField(),
                    "email": serializers.EmailField(),
                    "is_staff": serializers.BooleanField()
                }
            ),
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(description="Unauthorized"),
        }
    )
)
class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = MeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
