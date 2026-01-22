from rest_framework import serializers


class EntrepriseSerializer(serializers.Serializer):
    """Serializer complet pour une entreprise."""

    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(max_length=255)
    siret = serializers.CharField(max_length=14)
    is_active = serializers.BooleanField(default=True)
    created_at = serializers.DateTimeField(read_only=True)


class EntrepriseCreateSerializer(serializers.Serializer):
    """Serializer pour la création d'une entreprise."""

    name = serializers.CharField(max_length=255)
    siret = serializers.CharField(max_length=14)


class EntrepriseUpdateSerializer(serializers.Serializer):
    """Serializer pour la mise à jour d'une entreprise."""

    name = serializers.CharField(max_length=255, required=False)
    is_active = serializers.BooleanField(required=False)
