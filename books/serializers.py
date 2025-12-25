from decimal import Decimal
from rest_framework import serializers
from .models import Book

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ("id", "title", "author", "cover", "inventory", "daily_fee")

    def validate_inventory(self, value):
        if value <= 0:
            raise serializers.ValidationError("Inventory must be positive.")
        return value

    def validate_daily_fee(self, value):
        if value <= Decimal("0"):
            raise serializers.ValidationError("Daily fee must be positive.")
        return value
