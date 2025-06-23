from rest_framework import serializers

from library_management.library.models import Author, Book, Category, Library


class LibrarySerializer(serializers.ModelSerializer):
    distance = serializers.FloatField()

    class Meta:
        model = Library
        fields = ("id", "name", "address", "distance", "created", "modified")

    def to_representation(self, instance):
        """
        Override to include distance in kilometers in the representation.
        """
        if hasattr(instance, "distance"):
            instance.distance = round(
                instance.distance.km, 2
            )  # Convert meters to kilometers
        return super().to_representation(instance)


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for Category model.
    Assuming Category model has fields like name, description, etc.
    """

    class Meta:
        model = Category
        fields = (
            "id",
            "name",
            "description",
        )


class AuthorBookListSerializer(serializers.Serializer):
    """
    Serializer for Author model with book count.
    Assuming Author model has a related_name 'books' for Book model.
    """

    id = serializers.IntegerField()
    title = serializers.CharField()
    description = serializers.CharField()
    category = CategorySerializer()
    created = serializers.DateTimeField()
    modified = serializers.DateTimeField()


class AuthorListSerializer(serializers.ModelSerializer):
    book_counts = serializers.IntegerField()
    books = AuthorBookListSerializer(many=True, read_only=True)

    class Meta:
        model = Author
        fields = ("id", "name", "bio", "book_counts", "books", "created", "modified")


class BookListSerializer(serializers.ModelSerializer):
    """
    Serializer for Book model.
    Assuming Book model has fields like title, author, category, etc.
    """

    category_name = serializers.CharField()
    author_name = serializers.CharField()

    class Meta:
        model = Book
        fields = (
            "id",
            "title",
            "description",
            "author_name",
            "category_name",
            "created",
            "modified",
        )
