from django.conf import settings

from rest_framework import authentication, exceptions

import jwt

from apps.users.models import Role, User


class SupabaseJWTAuthentication(authentication.BaseAuthentication):
    """
    Authentification JWT Supabase pour Django REST Framework.
    Valide le token JWT et synchronise/crée l'utilisateur Django.
    """

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None

        try:
            prefix, token = auth_header.split(" ")
            if prefix.lower() != "bearer":
                return None
        except ValueError:
            return None

        try:
            payload = self._decode_jwt(token)
        except jwt.ExpiredSignatureError as err:
            raise exceptions.AuthenticationFailed("Token expiré") from err
        except jwt.InvalidTokenError as e:
            raise exceptions.AuthenticationFailed(f"Token invalide: {str(e)}") from e

        user = self._get_or_create_user(payload)
        return (user, token)

    def _decode_jwt(self, token):
        """Décode et valide le JWT Supabase."""
        jwt_secret = settings.SUPABASE_JWT_SECRET

        if not jwt_secret:
            raise exceptions.AuthenticationFailed("SUPABASE_JWT_SECRET non configuré")

        return jwt.decode(
            token,
            jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )

    def _get_or_create_user(self, payload):
        """
        Récupère ou crée un User Django à partir du payload JWT Supabase.
        username = sub (Supabase user ID)
        Rôle par défaut = GERANT_PME
        """
        sub = payload.get("sub")
        if not sub:
            raise exceptions.AuthenticationFailed("Token sans sub")

        email = payload.get("email", "")

        try:
            user = User.objects.get(username=sub)
            if email and user.email != email:
                user.email = email
                user.save(update_fields=["email"])
        except User.DoesNotExist:
            default_role = Role.objects.filter(code=Role.GERANT_PME).first()

            user = User.objects.create(
                username=sub,
                email=email,
                role=default_role,
            )

        return user

    def authenticate_header(self, request):
        return "Bearer"
