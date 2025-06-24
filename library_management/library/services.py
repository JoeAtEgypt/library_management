from datetime import date

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.db import transaction
from django.db.models import Count, F, Prefetch
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.serializers import ValidationError

from library_management.users.tasks import async_send_email

from .models import Author, Book, BorrowedBook, BorrowTransaction, Library


class LibraryService:
    @staticmethod
    def get_nearby_libraries(user_longitude, user_latitude):
        """
        Get libraries within 5km of the user's location.
        Args:
            user_latitude (float): Latitude of the user's location.
            user_longitude (float): Longitude of the user's location.
        Returns:
            QuerySet: Libraries within 5km of the user's location, ordered by distance.
        """

        user_location = Point(user_longitude, user_latitude, srid=4326)
        queryset = (
            Library.objects.annotate(
                distance=Distance("location", user_location, spheroid=True)
            )
            # .filter(distance__lte=20_000)  # in meters
            .order_by("distance")
        )
        # Print the distance for each library
        for library in queryset:
            print(f"{library.name}: {round(library.distance.km, 2)} km")

        return queryset


class AuthorService:
    @staticmethod
    def get_authors():
        return (
            Author.objects.prefetch_related(
                Prefetch("books", queryset=Book.objects.select_related("category"))
            )
            .annotate(book_counts=Count("books", distinct=True))
            .all()
        )

    # Add more queryset methods as needed


class BookService:
    @staticmethod
    def get_books():
        # Assuming Book is a model defined elsewhere
        return Book.objects.annotate(
            category_name=F("category__name"), author_name=F("author__name")
        ).all()  # Replace with actual logic to fetch books

    @staticmethod
    @transaction.atomic
    def borrow_a_book(user, book_id, return_due):
        if not book_id:
            raise ValidationError("No book ID provided")

        if not return_due:
            raise ValidationError("No return due date provided")

        return_due = date.fromisoformat(return_due)
        book = get_object_or_404(Book, id=book_id)

        transaction, created = BorrowTransaction.objects.get_or_create(user=user)
        if not created:
            transaction.borrowed_books_count += 1
            transaction.save()

        borrowed_book = BorrowedBook(
            transaction=transaction, book=book, return_due=return_due
        )
        borrowed_book.save()

        async_send_email.delay(
            subject="Book Borrowed",
            message=f"You have successfully borrowed the book with ID {book.id} and Name {book.title}.",  # noqa: E501
            receivers=[user.email],
        )

    @staticmethod
    @transaction.atomic
    def return_a_book(user, book_id):
        if not book_id:
            raise ValidationError("No book ID provided")

        borrowed_book = get_object_or_404(
            BorrowedBook,
            book__id=book_id,
            transaction__user=user,
            returned_at__isnull=True,
        )
        transaction = borrowed_book.transaction

        borrowed_book.returned_at = timezone.now()
        transaction.borrowed_books_count -= 1
        transaction.save()

        borrowed_book.save()

        # Notify the user about the book return
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "book_availability",
            {
                "type": "book_available",
                "message": f"The book '{borrowed_book.book.title}' was returned and is now available.",  # noqa: E501
            },
        )
        return borrowed_book.penalty
