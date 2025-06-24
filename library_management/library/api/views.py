from django.db.models import Q
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from library_management.library.filters import AuthorFilter, BookFilter, LibraryFilter
from library_management.library.models import Book
from library_management.library.services import (
    AuthorService,
    BookService,
    LibraryService,
)
from library_management.users.tasks import async_send_email

from .serializers import AuthorListSerializer, BookListSerializer, LibrarySerializer


class LibraryListView(generics.ListAPIView):
    """API view to list libraries with optional filtering by book category and author."""  # noqa: E501

    serializer_class = LibrarySerializer
    filterset_class = LibraryFilter

    def get_queryset(self):
        """
        Override to get the queryset based on user's location.
        Assumes user latitude and longitude are provided
        in the request query parameters.
        """
        user_latitude = self.request.query_params.get("latitude")
        user_longitude = self.request.query_params.get("longitude")

        if user_latitude and user_longitude:
            return LibraryService.get_nearby_libraries(
                user_longitude=float(user_longitude), user_latitude=float(user_latitude)
            )
        return super().get_queryset()


class AuthorListView(generics.ListAPIView):
    """API view to list authors with optional filtering by book category and author."""  # noqa: E501

    serializer_class = AuthorListSerializer
    filterset_class = AuthorFilter

    def get_queryset(self):
        """
        Override to get the queryset based on filters.
        """
        # Pull filters manually to use in annotation
        book_category = self.request.query_params.get("book_category")
        library = self.request.query_params.get("library")

        # Dynamic filter Q object
        filter_q = Q()
        if book_category:
            filter_q &= Q(books__category__name__iexact=book_category)
        if library:
            filter_q &= Q(books__library__name__iexact=library)

        return AuthorService.get_authors(filters=filter_q if filter_q else None)


class BookListView(generics.ListAPIView):
    """API view to list books with optional filtering by category and author."""

    # Assuming BookService and BookFilter are defined elsewhere
    queryset = BookService.get_books()
    serializer_class = BookListSerializer  # Assuming BookSerializer is defined
    filterset_class = BookFilter  # Assuming BookFilter is defined


class BorrowBookView(APIView):
    """API view to handle borrowing books."""

    def post(self, request, book_id, *args, **kwargs):
        """Handle borrowing books.
        Expects a list of book IDs in the request data.
        """
        BookService.borrow_a_book(
            user=request.user,
            book_id=book_id,
            return_due=request.data.get("return_due"),
        )

        return Response({"message": "Books borrowed successfully"}, status=200)


class ReturnBookView(APIView):
    """API view to handle borrowing books."""

    def post(self, request, book_id, *args, **kwargs):
        """Handle borrowing books.
        Expects a list of book IDs in the request data.
        """
        if not book_id:
            return Response({"error": "No book IDs provided"}, status=400)

        penalty = BookService.return_a_book(user=request.user, book_id=book_id)

        return Response(
            {"message": "Books returned successfully", "penalty": penalty}, status=200
        )
