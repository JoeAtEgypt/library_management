from django.contrib import admin
from django.contrib.gis import (
    admin as gis_admin,  # Import GIS admin if using GIS features
)

from .models import Author, Book, BorrowedBook, BorrowTransaction, Category, Library


@admin.register(Library)
class LibraryAdmin(gis_admin.GISModelAdmin):
    """Admin interface for Library model."""

    list_display = ("name", "address", "created", "modified")
    search_fields = ("name", "address")


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    """Admin interface for Author model."""

    list_display = ("name", "created", "modified")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin interface for Category model."""

    list_display = (
        "name",
        "description",
    )
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    """Admin interface for Book model."""

    list_display = (
        "title",
        "author",
        "category",
        "library",
        "created",
        "modified",
    )
    search_fields = ("title", "author__name", "category__name", "library__name")
    list_filter = ("author", "category", "library")
    ordering = ("title",)


@admin.register(BorrowTransaction)
class UserTransactionAdmin(admin.ModelAdmin):
    """Admin interface for BorrowTransaction model."""

    list_display = ("user", "borrowed_books_count", "created", "modified")
    search_fields = ("user__email",)
    ordering = ("created",)


@admin.register(BorrowedBook)
class BorrowedBookAdmin(admin.ModelAdmin):
    """Admin interface for BorrowedBook model."""

    list_display = ("transaction__user", "book", "return_due", "returned_at")
    search_fields = ("transaction__user__email", "book__title")
    list_filter = ("returned_at",)
    ordering = ("-return_due",)
