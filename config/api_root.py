from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.reverse import reverse

def _link(request, route_name: str, default_path: str) -> str:
    """
    Try to reverse a named URL; fall back to a static path if reversing fails.
    """
    try:
        return reverse(route_name, request=request)
    except Exception:
        return default_path

@api_view(["GET"])
@permission_classes([AllowAny])
def api_root(request, format=None):
    return Response({
        "books": _link(request, "books:book-list", "/api/books/"),
        "borrowings": _link(request, "borrowings:borrowing-list", "/api/borrowings/"),
        "users": {
            "register": _link(request, "users:register", "/users/register/"),
            "token": _link(request, "users:token", "/users/token/"),
            "me": _link(request, "users:me", "/users/me/"),
        },
        "schema": _link(request, "schema", "/schema/"),
        "docs": "/docs/",
        "health": "/healthz/",
    })
