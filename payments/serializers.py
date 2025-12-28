from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = (
            "id",
            "borrowing",
            "type",
            "status",
            "amount",
            "session_url",
            "session_id",
            "paid_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "status",
            "session_url",
            "session_id",
            "paid_at",
            "created_at",
            "updated_at",
        )

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0.")
        return value

    def validate_type(self, value):
        choices = {c[0] for c in Payment.TYPE_CHOICES}
        if value not in choices:
            raise serializers.ValidationError("Invalid payment type.")
        return value
