from datetime import timedelta

from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.db import models
from django.db.models import Q, UniqueConstraint
from django.utils import timezone
from model_utils.models import TimeStampedModel
from rest_framework.serializers import ValidationError


# Create your models here.
class Library(TimeStampedModel):
    """Model representing a Library in the system."""

    name = models.CharField(max_length=100, unique=True)
    address = models.CharField(max_length=255)
    location = gis_models.PointField(geography=True, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Library"
        verbose_name_plural = "Libraries"


class Author(TimeStampedModel):
    """Model representing an Author in the system."""

    name = models.CharField(max_length=100)
    bio = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    """Model representing a Category in the system."""

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"


class Book(TimeStampedModel):
    """Model representing a Book in the system."""

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="books")
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="books",
    )
    library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name="books")

    def __str__(self):
        return self.title


class BorrowTransaction(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    borrowed_books_count = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Borrow Transaction"
        verbose_name_plural = "Borrow Transactions"

    def clean(self):
        if self.borrowed_books_count > 3:
            raise ValidationError(
                "User cannot borrow more than 3 books at a time. "
                "Return one to borrow a 4th"
            )
        return super().clean()

    def save(self, *args, **kwargs):
        """Override save method to ensure full clean is called."""
        self.full_clean()
        super().save(*args, **kwargs)


class BorrowedBook(models.Model):
    transaction = models.ForeignKey(
        BorrowTransaction, on_delete=models.CASCADE, related_name="borrowed_books"
    )
    book = models.ForeignKey(Book, on_delete=models.CASCADE)

    borrow_date = models.DateTimeField(auto_now_add=True)
    return_due = models.DateTimeField()  # must be <= borrow_date + 30 days
    returned_at = models.DateTimeField(null=True, blank=True)

    penalty_per_day = models.DecimalField(max_digits=6, decimal_places=2, default=0.5)

    class Meta:
        verbose_name = "Borrowed Book"
        verbose_name_plural = "Borrowed Books"
        constraints = [
            UniqueConstraint(
                fields=["transaction", "book"],
                condition=Q(returned_at__isnull=True),
                name="unique_active_borrowed_book",
            )
        ]

    @property
    def is_overdue(self):
        return not self.returned_at and timezone.now() > self.return_due

    @property
    def penalty(self):
        if self.returned_at and self.returned_at > self.return_due:
            days_late = (self.returned_at - self.return_due).days
            return round(days_late * self.penalty_per_day, 2)
        elif self.is_overdue:
            days_late = (timezone.now() - self.return_due).days
            return round(days_late * self.penalty_per_day, 2)
        return 0

    @property
    def is_returned(self):
        return self.returned_at is not None

    def clean(self):
        if self.return_due > timezone.now() + timedelta(days=30):
            raise ValidationError("Return date can't exceed 30 days from now.")

        if self.return_due < timezone.now():
            raise ValidationError("Return date can't be in the past.")

        return super().clean()

    def save(self, *args, **kwargs):
        """Override save method to ensure full clean is called."""

        self.full_clean()
        super().save(*args, **kwargs)
