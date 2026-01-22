import hashlib
from rest_framework.throttling import SimpleRateThrottle


def _user_cache_ident(user) -> str:
    raw = f"{user.pk}|{user.email}|{user.password}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class PaymentBurstThrottle(SimpleRateThrottle):
    scope = "payments_burst"

    def get_cache_key(self, request, view):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return None
        ident = _user_cache_ident(user)
        return f"throttle:{self.scope}:{ident}"


class PaymentSustainedThrottle(SimpleRateThrottle):
    scope = "payments_sustained"

    def get_cache_key(self, request, view):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return None
        ident = _user_cache_ident(user)
        return f"throttle:{self.scope}:{ident}"
