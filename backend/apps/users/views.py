from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.common.serializers import ErrorSerializer

from .serializers import UserResponseSerializer


@extend_schema(
    tags=["User"],
    summary="Obtenir le profil utilisateur",
    description="Retourne les informations de l'utilisateur authentifié via son JWT Supabase.",
    responses={
        200: UserResponseSerializer,
        401: ErrorSerializer,
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    """
    GET /api/v1/me
    Retourne les infos de l'utilisateur authentifié.
    """
    user = request.user
    return Response(
        {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role.code if user.role else None,
            "entreprise": (
                {
                    "id": str(user.entreprise.id),
                    "name": user.entreprise.name,
                    "siret": user.entreprise.siret,
                }
                if user.entreprise
                else None
            ),
            "created_at": user.created_at.isoformat(),
        }
    )
