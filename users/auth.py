from rest_framework_simplejwt.authentication import JWTAuthentication

class DualHeaderJWTAuthentication(JWTAuthentication):
    def get_header(self, request):
        header = super().get_header(request)
        if header is not None:
            return header
        alt = request.META.get("HTTP_AUTHORIZE")
        if isinstance(alt, str):
            return alt.encode()
        return alt
