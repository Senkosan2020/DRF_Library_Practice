from rest_framework.throttling import UserRateThrottle

class BasePerUserThrottle(UserRateThrottle):
    def get_cache_key(self, request, view):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return None
        ident = f"{user.pk}:{int(user.date_joined.timestamp())}"
        return self.cache_format % {"scope": self.scope, "ident": ident}

class BorrowingBurstThrottle(BasePerUserThrottle):
    scope = "borrowing_burst"

class BorrowingSustainedThrottle(BasePerUserThrottle):
    scope = "borrowing_sustained"

class ReturnBurstThrottle(BasePerUserThrottle):
    scope = "return_burst"

class ReturnSustainedThrottle(BasePerUserThrottle):
    scope = "return_sustained"
