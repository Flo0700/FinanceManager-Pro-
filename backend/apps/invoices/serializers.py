from rest_framework import serializers


class CustomerSerializer(serializers.Serializer):
    """Serializer pour un client."""

    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(max_length=255)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)
    vat_number = serializers.CharField(max_length=32, required=False, allow_blank=True)
    created_at = serializers.DateTimeField(read_only=True)


class InvoiceLineSerializer(serializers.Serializer):
    """Serializer pour une ligne de facture."""

    id = serializers.UUIDField(read_only=True)
    label = serializers.CharField(max_length=255)
    qty = serializers.DecimalField(max_digits=10, decimal_places=2)
    unit_price = serializers.DecimalField(max_digits=12, decimal_places=2)
    vat_rate = serializers.DecimalField(max_digits=5, decimal_places=2, default=20)
    total_ht = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_tva = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    total_ttc = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )


class InvoiceSerializer(serializers.Serializer):
    """Serializer pour une facture."""

    id = serializers.UUIDField(read_only=True)
    number = serializers.CharField(max_length=50, read_only=True)
    status = serializers.ChoiceField(choices=["DRAFT", "ISSUED", "PAID", "CANCELED"])
    customer_id = serializers.UUIDField()
    issue_date = serializers.DateField()
    due_date = serializers.DateField(required=False, allow_null=True)
    total_ht = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_tva = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    total_ttc = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    lines = InvoiceLineSerializer(many=True, read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class InvoiceCreateSerializer(serializers.Serializer):
    """Serializer pour la création d'une facture."""

    customer_id = serializers.UUIDField()
    issue_date = serializers.DateField(required=False)
    due_date = serializers.DateField(required=False, allow_null=True)
    lines = InvoiceLineSerializer(many=True)


class InvoiceListSerializer(serializers.Serializer):
    """Serializer pour la liste des factures."""

    id = serializers.UUIDField()
    number = serializers.CharField()
    status = serializers.CharField()
    customer_name = serializers.CharField()
    issue_date = serializers.DateField()
    due_date = serializers.DateField(allow_null=True)
    total_ttc = serializers.DecimalField(max_digits=12, decimal_places=2)
    created_at = serializers.DateTimeField()
