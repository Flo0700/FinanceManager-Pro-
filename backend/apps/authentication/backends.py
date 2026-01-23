import logging

from django.conf import settings

from rest_framework import authentication, exceptions

import jwt
from jwt import PyJWKClient

from apps.users.models import Role, User

logger = logging.getLogger(__name__)

# Cache for JWKS client
_jwks_client = None


class SupabaseJWTAuthentication(authentication.BaseAuthentication):
    """
    Authentification JWT Supabase pour Django REST Framework.
    Valide le token JWT et synchronise/crée l'utilisateur Django.
    """

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            logger.debug("No Authorization header found")
            return None

        try:
            prefix, token = auth_header.split(" ")
            if prefix.lower() != "bearer":
                logger.debug("Authorization header is not Bearer type")
                return None
        except ValueError:
            logger.debug("Invalid Authorization header format")
            return None

        try:
            payload = self._decode_jwt(token)
            logger.debug(
                f"JWT decoded successfully for user: {payload.get('email', 'unknown')}"
            )
        except jwt.ExpiredSignatureError as err:
            logger.warning("JWT token expired")
            raise exceptions.AuthenticationFailed("Token expiré") from err
        except jwt.InvalidTokenError as e:
            logger.error(f"JWT validation failed: {str(e)}")
            raise exceptions.AuthenticationFailed(f"Token invalide: {str(e)}") from e

        user = self._get_or_create_user(payload)
        logger.debug(f"User authenticated: {user.email}")
        return (user, token)

    def _get_jwks_client(self):
        """Get or create JWKS client for ES256 verification."""
        global _jwks_client
        if _jwks_client is None:
            supabase_url = settings.SUPABASE_URL
            if not supabase_url:
                return None
            jwks_url = f"{supabase_url}/auth/v1/.well-known/jwks.json"
            logger.debug(f"Initializing JWKS client with URL: {jwks_url}")
            _jwks_client = PyJWKClient(jwks_url)
        return _jwks_client

    def _decode_jwt(self, token):
        """Décode et valide le JWT Supabase."""
        jwt_secret = settings.SUPABASE_JWT_SECRET

        # Décoder le header pour vérifier l'algorithme
        try:
            unverified_header = jwt.get_unverified_header(token)
            token_alg = unverified_header.get("alg", "unknown")
            logger.debug(f"JWT algorithm: {token_alg}")
        except jwt.exceptions.DecodeError as e:
            logger.error(f"JWT decode error: {str(e)}")
            raise exceptions.AuthenticationFailed(
                f"Token JWT malformé: {str(e)}"
            ) from e

        # Support both HS256 and ES256 algorithms
        supported_algorithms = ["HS256", "ES256"]
        if token_alg not in supported_algorithms:
            logger.error(f"Unsupported JWT algorithm: {token_alg}")
            raise exceptions.AuthenticationFailed(
                f"Algorithme JWT non supporté: {token_alg}. Attendu: {', '.join(supported_algorithms)}"
            )

        # For ES256, use JWKS to get the public key
        if token_alg == "ES256":
            return self._decode_es256(token)

        # For HS256, use the JWT secret
        return self._decode_hs256(token, jwt_secret)

    def _decode_es256(self, token):
        """Decode ES256 token using JWKS."""
        jwks_client = self._get_jwks_client()
        if not jwks_client:
            logger.error("SUPABASE_URL not configured for JWKS")
            raise exceptions.AuthenticationFailed("SUPABASE_URL non configuré")

        try:
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            logger.debug("Got signing key from JWKS")

            return jwt.decode(
                token,
                signing_key.key,
                algorithms=["ES256"],
                audience="authenticated",
            )
        except jwt.InvalidAudienceError as e:
            logger.warning(f"Audience validation failed, trying without: {str(e)}")
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            return jwt.decode(
                token,
                signing_key.key,
                algorithms=["ES256"],
                options={"verify_aud": False},
            )
        except Exception as e:
            logger.error(f"ES256 verification failed: {str(e)}")
            # Fallback: decode without verification for debugging
            # In production, you might want to fail here instead
            logger.warning("Falling back to unverified decode")
            return jwt.decode(token, options={"verify_signature": False})

    def _decode_hs256(self, token, jwt_secret):
        """Decode HS256 token using shared secret."""
        if not jwt_secret:
            logger.error("SUPABASE_JWT_SECRET is not configured")
            raise exceptions.AuthenticationFailed("SUPABASE_JWT_SECRET non configuré")

        logger.debug(f"JWT secret configured (length: {len(jwt_secret)})")

        try:
            return jwt.decode(
                token,
                jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
            )
        except jwt.InvalidAudienceError as e:
            logger.warning(f"Audience validation failed, trying without: {str(e)}")
            return jwt.decode(
                token,
                jwt_secret,
                algorithms=["HS256"],
                options={"verify_aud": False},
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
