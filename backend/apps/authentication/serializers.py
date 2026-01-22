from rest_framework import serializers


class AuthCredentialsSerializer(serializers.Serializer):
    """Serializer pour les credentials d'authentification."""

    email = serializers.EmailField(help_text="Adresse email de l'utilisateur")
    password = serializers.CharField(help_text="Mot de passe (min 6 caractères)")


class RefreshTokenSerializer(serializers.Serializer):
    """Serializer pour le rafraîchissement de token."""

    refresh_token = serializers.CharField(
        help_text="Token de rafraîchissement Supabase"
    )


class AuthTokenResponseSerializer(serializers.Serializer):
    """Serializer pour la réponse d'authentification."""

    access_token = serializers.CharField(help_text="JWT d'accès")
    token_type = serializers.CharField(default="bearer")
    expires_in = serializers.IntegerField(help_text="Durée de validité en secondes")
    refresh_token = serializers.CharField(help_text="Token pour rafraîchir l'accès")
    user = serializers.DictField(help_text="Informations utilisateur Supabase")


class GoogleAuthResponseSerializer(serializers.Serializer):
    """Serializer pour la réponse OAuth Google."""

    url = serializers.URLField(help_text="URL de redirection OAuth Google")
    message = serializers.CharField()


class LogoutResponseSerializer(serializers.Serializer):
    """Serializer pour la réponse de déconnexion."""

    message = serializers.CharField(default="Déconnecté")
