from django.conf import settings
from django.urls import path
from rest_framework.routers import DefaultRouter, SimpleRouter

from library_management.library.api.views import (
    AuthorListView,
    BookListView,
    BorrowBookView,
    LibraryListView,
    ReturnBookView,
)
from library_management.users.api.views import (
    PasswordResetView,
    RegisterView,
    UserViewSet,
)

router = DefaultRouter() if settings.DEBUG else SimpleRouter()

# User APIs
router.register("users", UserViewSet)


app_name = "api"
urlpatterns = [
    # User registration endpoint
    path("users/register/", RegisterView.as_view(), name="register"),
    # Password reset endpoint
    path(
        "users/reset-password/",
        PasswordResetView.as_view(),
        name="reset_forget_password",
    ),
    # Library APIs
    path("libraries/", LibraryListView.as_view(), name="library-list"),
    path("authors/", AuthorListView.as_view(), name="authors-list"),
    path("books/", BookListView.as_view(), name="books-list"),
    path("borrow/<book_id>", BorrowBookView.as_view(), name="borrow-book"),
    path("return/<book_id>", ReturnBookView.as_view(), name="return-book"),
    *router.urls,
]
