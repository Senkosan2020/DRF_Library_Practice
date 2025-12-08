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


class BorrowingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = ("id", "borrow_date", "expected_return_date", "book")

    def validate(self, attrs):
        borrow_date = attrs.get("borrow_date")
        expected = attrs.get("expected_return_date")
        if expected and borrow_date and expected < borrow_date:
            raise serializers.ValidationError("expected_return_date must be >= borrow_date")

        book = attrs.get("book")
        if book and book.inventory <= 0:
            raise serializers.ValidationError({"book": "No inventory available for this book"})
        return attrs
