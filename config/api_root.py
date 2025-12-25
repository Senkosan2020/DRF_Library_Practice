from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
def api_root(request):
    def abs_url(path: str) -> str:
        return request.build_absolute_uri(path)

    return Response({
        "resources": {
            "books": abs_url("/api/books/"),
            "borrowings": abs_url("/api/borrowings/"),
        },
        "users": {
            "register": abs_url("/users/register/"),
            "token_obtain_pair": abs_url("/users/token/"),
            "token_refresh": abs_url("/users/token/refresh/"),
            "me": abs_url("/users/me/"),
        },
        "docs": abs_url("/docs/"),
        "schema": abs_url("/schema/"),
        "health": abs_url("/health/"),
        "healthz": abs_url("/healthz/"),
    })
