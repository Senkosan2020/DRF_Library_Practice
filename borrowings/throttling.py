import hashlib
from rest_framework.throttling import SimpleRateThrottle

def _user_cache_ident(user) -> str:
    raw = f"{user.pk}|{user.email}|{user.password}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

class BorrowingBurstThrottle(SimpleRateThrottle):
    scope = "borrowing_burst"

    def get_cache_key(self, request, view):
        u = getattr(request, "user", None)
        if not u or not u.is_authenticated:
            return None
        ident = _user_cache_ident(u)
        return f"throttle:{self.scope}:{ident}"


class BorrowingSustainedThrottle(SimpleRateThrottle):
    scope = "borrowing_sustained"

    def get_cache_key(self, request, view):
        u = getattr(request, "user", None)
        if not u or not u.is_authenticated:
            return None
        ident = _user_cache_ident(u)
        return f"throttle:{self.scope}:{ident}"


class ReturnBurstThrottle(SimpleRateThrottle):
    scope = "return_burst"

    def get_cache_key(self, request, view):
        u = getattr(request, "user", None)
        if not u or not u.is_authenticated:
            return None
        ident = _user_cache_ident(u)
        return f"throttle:{self.scope}:{ident}"


class ReturnSustainedThrottle(SimpleRateThrottle):
    scope = "return_sustained"

    def get_cache_key(self, request, view):
        u = getattr(request, "user", None)
        if not u or not u.is_authenticated:
            return None
        ident = _user_cache_ident(u)
        return f"throttle:{self.scope}:{ident}"
