from rest_framework import serializers


class RoleSerializer(serializers.Serializer):
    """Serializer pour les rôles."""

    id = serializers.UUIDField(read_only=True)
    code = serializers.CharField()
    label = serializers.CharField()
    description = serializers.CharField()


class EntrepriseMinimalSerializer(serializers.Serializer):
    """Serializer minimal pour l'entreprise dans le contexte utilisateur."""

    id = serializers.UUIDField()
    name = serializers.CharField()
    siret = serializers.CharField()


class UserResponseSerializer(serializers.Serializer):
    """Serializer pour la réponse utilisateur."""

    id = serializers.UUIDField(help_text="UUID de l'utilisateur")
    username = serializers.CharField(help_text="Supabase sub (user ID)")
    email = serializers.EmailField()
    role = serializers.CharField(allow_null=True, help_text="Code du rôle")
    entreprise = EntrepriseMinimalSerializer(allow_null=True)
    created_at = serializers.DateTimeField()


class UserListSerializer(serializers.Serializer):
    """Serializer pour la liste des utilisateurs."""

    id = serializers.UUIDField()
    username = serializers.CharField()
    email = serializers.EmailField()
    role = serializers.CharField(allow_null=True)
    is_active = serializers.BooleanField()
    created_at = serializers.DateTimeField()
