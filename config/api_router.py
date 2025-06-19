from django.conf import settings
from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework.routers import SimpleRouter

from library_management.users.api.views import RegisterView
from library_management.users.api.views import UserViewSet

router = DefaultRouter() if settings.DEBUG else SimpleRouter()

# User APIs
router.register("users", UserViewSet)


app_name = "api"
urlpatterns = [
    # User registration endpoint
    path("users/register/", RegisterView.as_view(), name="register"),
    *router.urls,
]
