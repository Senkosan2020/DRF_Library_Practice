from decimal import Decimal
from borrowings.models import Borrowing
from borrowings.serializers import BorrowingReadSerializer
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


class PaymentReadSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    borrowing = serializers.PrimaryKeyRelatedField(read_only=True)
    amount = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    def get_amount(self, obj):
        value = getattr(obj, "amount", None)
        return str(value) if value is not None else None

    def get_status(self, obj):
        return getattr(obj, "status", None)


class PaymentCreateSerializer(serializers.Serializer):
    borrowing = serializers.PrimaryKeyRelatedField(queryset=Borrowing.objects.all())

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        borrowing = attrs["borrowing"]

        if not user or not user.is_authenticated:
            raise serializers.ValidationError({"detail": "Authentication required."})

        if not (user.is_staff or borrowing.user_id == user.id):
            raise serializers.ValidationError({"detail": "Forbidden."})

        qs = Payment.objects.filter(borrowing=borrowing)
        if hasattr(Payment, "status"):
            pending = getattr(Payment, "PENDING", "PENDING")
            qs = qs.filter(status=pending)
        if qs.exists():
            raise serializers.ValidationError(
                {"detail": "An open payment already exists for this borrowing."}
            )

        attrs["user"] = user
        return attrs

    def create(self, validated_data):
        borrowing = validated_data["borrowing"]
        user = validated_data["user"]

        # derive amount from borrowing's late_fee if present
        amount = None
        data = BorrowingReadSerializer(borrowing).data
        if "late_fee" in data and data["late_fee"] is not None:
            try:
                amount = Decimal(str(data["late_fee"]))
            except Exception:
                amount = None

        payment = Payment(borrowing=borrowing)
        if hasattr(payment, "user"):
            payment.user = user
        if hasattr(payment, "amount") and amount is not None:
            payment.amount = amount
        if hasattr(payment, "status"):
            payment.status = getattr(Payment, "PENDING", "PENDING")
        payment.save()
        return payment
