from rest_framework import serializers
from .models import Borrowing
from books.models import Book

class BookShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ("id", "title", "author", "cover")

class BorrowingReadSerializer(serializers.ModelSerializer):
    book = BookShortSerializer(read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "is_active",
            "book",
            "user",
        )
        read_only_fields = ("user",)
