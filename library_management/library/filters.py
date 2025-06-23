from django_filters import rest_framework as filters

from .models import Author, Book, Library


class LibraryFilter(filters.FilterSet):
    book_category = filters.CharFilter(
        field_name="books__category__name",
        lookup_expr="iexact",
    )
    author = filters.CharFilter(field_name="books__author__name", lookup_expr="iexact")

    class Meta:
        model = Library
        fields = ["book_category", "author"]


class AuthorFilter(filters.FilterSet):
    book_category = filters.CharFilter(
        field_name="books__category__name",
        lookup_expr="iexact",
    )
    library = filters.CharFilter(
        field_name="books__library__name", lookup_expr="iexact"
    )

    class Meta:
        model = Author
        fields = ["book_category", "library"]


class BookFilter(filters.FilterSet):
    library = filters.CharFilter(
        field_name="library__name",
        lookup_expr="iexact",
    )
    author = filters.CharFilter(
        field_name="author__name",
        lookup_expr="iexact",
    )
    category = filters.CharFilter(
        field_name="category__name",
        lookup_expr="iexact",
    )

    class Meta:
        model = Book
        fields = ["library", "author", "category"]
