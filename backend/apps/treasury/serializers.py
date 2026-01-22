from rest_framework import serializers


class BankTransactionSerializer(serializers.Serializer):
    """Serializer pour une transaction bancaire."""

    id = serializers.UUIDField(read_only=True)
    date = serializers.DateField()
    label = serializers.CharField(max_length=255)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    created_at = serializers.DateTimeField(read_only=True)


class BankTransactionCreateSerializer(serializers.Serializer):
    """Serializer pour la création d'une transaction."""

    date = serializers.DateField(required=False)
    label = serializers.CharField(max_length=255)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)


class ReconciliationSerializer(serializers.Serializer):
    """Serializer pour un rapprochement."""

    id = serializers.UUIDField(read_only=True)
    invoice_id = serializers.UUIDField()
    bank_transaction_id = serializers.UUIDField()
    matched_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    matched_at = serializers.DateTimeField(read_only=True)
    matched_by_id = serializers.UUIDField(read_only=True)


class ReconciliationCreateSerializer(serializers.Serializer):
    """Serializer pour la création d'un rapprochement."""

    invoice_id = serializers.UUIDField()
    bank_transaction_id = serializers.UUIDField()
    matched_amount = serializers.DecimalField(max_digits=12, decimal_places=2)


class TreasuryDashboardSerializer(serializers.Serializer):
    """Serializer pour le dashboard trésorerie."""

    balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_in = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_out = serializers.DecimalField(max_digits=12, decimal_places=2)
    recent_transactions = BankTransactionSerializer(many=True)
