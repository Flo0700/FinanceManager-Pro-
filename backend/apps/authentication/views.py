import requests
from django.conf import settings
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.common.serializers import ErrorSerializer

from .serializers import (
    AuthCredentialsSerializer,
    AuthTokenResponseSerializer,
    GoogleAuthResponseSerializer,
    LogoutResponseSerializer,
    RefreshTokenSerializer,
)


@extend_schema(
    tags=["Auth"],
    summary="Inscription utilisateur",
    description="Crée un nouveau compte utilisateur via Supabase avec email et mot de passe.",
    request=AuthCredentialsSerializer,
    responses={
        201: AuthTokenResponseSerializer,
        400: ErrorSerializer,
        500: ErrorSerializer,
    },
    examples=[
        OpenApiExample(
            "Exemple de requête",
            value={"email": "user@example.com", "password": "securepassword123"},
            request_only=True,
        ),
    ],
)
@api_view(["POST"])
@permission_classes([AllowAny])
def auth_register(request):
    """
    POST /api/v1/auth/register
    Inscription via Supabase (email/password).
    """
    email = request.data.get("email")
    password = request.data.get("password")

    if not email or not password:
        return Response(
            {"error": "Email et password requis"}, status=status.HTTP_400_BAD_REQUEST
        )

    supabase_url = settings.SUPABASE_URL
    supabase_key = settings.SUPABASE_KEY

    if not supabase_url or not supabase_key:
        return Response(
            {"error": "Supabase non configuré"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    response = requests.post(
        f"{supabase_url}/auth/v1/signup",
        json={"email": email, "password": password},
        headers={
            "apikey": supabase_key,
            "Content-Type": "application/json",
        },
    )

    if response.status_code >= 400:
        return Response(response.json(), status=response.status_code)

    return Response(response.json(), status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["Auth"],
    summary="Connexion utilisateur",
    description="Authentifie un utilisateur via Supabase avec email et mot de passe. Retourne un JWT d'accès.",
    request=AuthCredentialsSerializer,
    responses={
        200: AuthTokenResponseSerializer,
        400: ErrorSerializer,
        401: ErrorSerializer,
        500: ErrorSerializer,
    },
    examples=[
        OpenApiExample(
            "Exemple de requête",
            value={"email": "user@example.com", "password": "securepassword123"},
            request_only=True,
        ),
    ],
)
@api_view(["POST"])
@permission_classes([AllowAny])
def auth_login(request):
    """
    POST /api/v1/auth/login
    Connexion via Supabase (email/password).
    """
    email = request.data.get("email")
    password = request.data.get("password")

    if not email or not password:
        return Response(
            {"error": "Email et password requis"}, status=status.HTTP_400_BAD_REQUEST
        )

    supabase_url = settings.SUPABASE_URL
    supabase_key = settings.SUPABASE_KEY

    if not supabase_url or not supabase_key:
        return Response(
            {"error": "Supabase non configuré"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    response = requests.post(
        f"{supabase_url}/auth/v1/token?grant_type=password",
        json={"email": email, "password": password},
        headers={
            "apikey": supabase_key,
            "Content-Type": "application/json",
        },
    )

    if response.status_code >= 400:
        return Response(response.json(), status=response.status_code)

    return Response(response.json(), status=status.HTTP_200_OK)


@extend_schema(
    tags=["Auth"],
    summary="Authentification Google OAuth",
    description="Retourne l'URL de redirection pour l'authentification via Google OAuth (Supabase).",
    parameters=[
        OpenApiParameter(
            name="redirect_to",
            type=OpenApiTypes.URI,
            location=OpenApiParameter.QUERY,
            description="URL de callback après authentification Google",
            required=False,
        ),
    ],
    responses={
        200: GoogleAuthResponseSerializer,
        500: ErrorSerializer,
    },
)
@api_view(["GET"])
@permission_classes([AllowAny])
def auth_google(request):
    """
    GET /api/v1/auth/google
    Retourne l'URL de redirection pour l'auth Google via Supabase.
    """
    supabase_url = settings.SUPABASE_URL
    supabase_key = settings.SUPABASE_KEY

    if not supabase_url or not supabase_key:
        return Response(
            {"error": "Supabase non configuré"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    redirect_to = request.query_params.get("redirect_to", "")

    # Build OAuth URL with required apikey parameter
    auth_url = f"{supabase_url}/auth/v1/authorize?provider=google&apikey={supabase_key}"
    if redirect_to:
        from urllib.parse import quote

        auth_url += f'&redirect_to={quote(redirect_to, safe="")}'

    return Response(
        {
            "url": auth_url,
            "message": "Redirigez l'utilisateur vers cette URL pour l'auth Google",
        }
    )


@extend_schema(
    tags=["Auth"],
    summary="Rafraîchir le token",
    description="Utilise le refresh_token pour obtenir un nouveau JWT d'accès.",
    request=RefreshTokenSerializer,
    responses={
        200: AuthTokenResponseSerializer,
        400: ErrorSerializer,
        401: ErrorSerializer,
        500: ErrorSerializer,
    },
)
@api_view(["POST"])
@permission_classes([AllowAny])
def auth_refresh(request):
    """
    POST /api/v1/auth/refresh
    Rafraîchit le token d'accès via Supabase.
    """
    refresh_token = request.data.get("refresh_token")

    if not refresh_token:
        return Response(
            {"error": "refresh_token requis"}, status=status.HTTP_400_BAD_REQUEST
        )

    supabase_url = settings.SUPABASE_URL
    supabase_key = settings.SUPABASE_KEY

    if not supabase_url or not supabase_key:
        return Response(
            {"error": "Supabase non configuré"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    response = requests.post(
        f"{supabase_url}/auth/v1/token?grant_type=refresh_token",
        json={"refresh_token": refresh_token},
        headers={
            "apikey": supabase_key,
            "Content-Type": "application/json",
        },
    )

    if response.status_code >= 400:
        return Response(response.json(), status=response.status_code)

    return Response(response.json(), status=status.HTTP_200_OK)


@extend_schema(
    tags=["Auth"],
    summary="Déconnexion",
    description="Invalide le token d'accès côté Supabase. Requiert un JWT valide.",
    responses={
        200: LogoutResponseSerializer,
        401: ErrorSerializer,
        500: ErrorSerializer,
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def auth_logout(request):
    """
    POST /api/v1/auth/logout
    Déconnexion (invalide le token côté Supabase).
    """
    supabase_url = settings.SUPABASE_URL
    supabase_key = settings.SUPABASE_KEY

    if not supabase_url or not supabase_key:
        return Response(
            {"error": "Supabase non configuré"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    auth_header = request.headers.get("Authorization", "")

    requests.post(
        f"{supabase_url}/auth/v1/logout",
        headers={
            "apikey": supabase_key,
            "Authorization": auth_header,
            "Content-Type": "application/json",
        },
    )

    return Response({"message": "Déconnecté"}, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Auth"],
    summary="Vérifier le statut de l'email",
    description="Vérifie si l'email de l'utilisateur connecté a été vérifié via Supabase.",
    responses={
        200: {
            "type": "object",
            "properties": {
                "email_verified": {"type": "boolean"},
                "email": {"type": "string"},
            },
        },
        401: ErrorSerializer,
        500: ErrorSerializer,
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def auth_verify_email_status(request):
    """
    GET /api/v1/auth/verify-email-status
    Vérifie si l'email de l'utilisateur a été confirmé.
    """
    supabase_url = settings.SUPABASE_URL
    supabase_key = settings.SUPABASE_KEY

    if not supabase_url or not supabase_key:
        return Response(
            {"error": "Supabase non configuré"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    auth_header = request.headers.get("Authorization", "")

    # Récupérer les infos utilisateur depuis Supabase
    response = requests.get(
        f"{supabase_url}/auth/v1/user",
        headers={
            "apikey": supabase_key,
            "Authorization": auth_header,
        },
    )

    if response.status_code >= 400:
        return Response(response.json(), status=response.status_code)

    user_data = response.json()
    email_confirmed_at = user_data.get("email_confirmed_at")

    return Response(
        {
            "email_verified": email_confirmed_at is not None,
            "email": user_data.get("email", ""),
            "confirmed_at": email_confirmed_at,
        },
        status=status.HTTP_200_OK,
    )


@extend_schema(
    tags=["Auth"],
    summary="Renvoyer l'email de vérification",
    description="Renvoie l'email de vérification à l'utilisateur via Supabase.",
    request={
        "type": "object",
        "properties": {
            "email": {"type": "string", "format": "email"},
        },
        "required": ["email"],
    },
    responses={
        200: {"type": "object", "properties": {"message": {"type": "string"}}},
        400: ErrorSerializer,
        500: ErrorSerializer,
    },
)
@api_view(["POST"])
@permission_classes([AllowAny])
def auth_resend_verification(request):
    """
    POST /api/v1/auth/resend-verification
    Renvoie l'email de vérification.
    """
    email = request.data.get("email")

    if not email:
        return Response({"error": "Email requis"}, status=status.HTTP_400_BAD_REQUEST)

    supabase_url = settings.SUPABASE_URL
    supabase_key = settings.SUPABASE_KEY

    if not supabase_url or not supabase_key:
        return Response(
            {"error": "Supabase non configuré"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    response = requests.post(
        f"{supabase_url}/auth/v1/resend",
        json={"type": "signup", "email": email},
        headers={
            "apikey": supabase_key,
            "Content-Type": "application/json",
        },
    )

    if response.status_code >= 400:
        return Response(response.json(), status=response.status_code)

    return Response(
        {"message": "Email de vérification envoyé"},
        status=status.HTTP_200_OK,
    )
