from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
def api_root(request):
    uri = request.build_absolute_uri

    return Response({
        "resources": {
            "books": uri("/api/books/"),
            "borrowings": uri("/api/borrowings/"),
        },
        "users": {
            "register": uri("/users/register/"),
            "token_obtain_pair": uri("/users/token/"),
            "token_refresh": uri("/users/token/refresh/"),
            "me": uri("/users/me/"),
        },
        "docs": uri("/docs/"),
        "schema": uri("/schema/"),
        "health": uri("/health/"),
        "healthz": uri("/healthz/"),
    })
