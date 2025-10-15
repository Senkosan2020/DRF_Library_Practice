from django.urls import path
from .views import RegisterView, MeView

urlpatterns = [
    path("", RegisterView.as_view(), name="users-register"),
    path("me/", MeView.as_view(), name="users-me"),
]