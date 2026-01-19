from rest_framework import serializers


class ErrorSerializer(serializers.Serializer):
    """Serializer générique pour les erreurs."""
    error = serializers.CharField(help_text="Message d'erreur")


class MessageSerializer(serializers.Serializer):
    """Serializer générique pour les messages."""
    message = serializers.CharField(help_text="Message de confirmation")
