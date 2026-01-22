from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.common.serializers import ErrorSerializer

from .models import Entreprise
from .serializers import EntrepriseCreateSerializer, EntrepriseSerializer


@extend_schema(
    tags=["Companies"],
    summary="Lister les entreprises",
    description="Retourne la liste des entreprises (ADMIN_CABINET uniquement).",
    responses={
        200: EntrepriseSerializer(many=True),
        401: ErrorSerializer,
        403: ErrorSerializer,
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def company_list(request):
    """
    GET /api/v1/companies
    Liste des entreprises (admin cabinet).
    """
    # TODO: Vérifier rôle ADMIN_CABINET
    companies = Entreprise.objects.filter(is_active=True).order_by("name")
    data = [
        {
            "id": str(c.id),
            "name": c.name,
            "siret": c.siret,
            "is_active": c.is_active,
            "created_at": c.created_at.isoformat(),
        }
        for c in companies
    ]
    return Response(data)


@extend_schema(
    tags=["Companies"],
    summary="Créer une entreprise",
    description="Crée une nouvelle entreprise (ADMIN_CABINET uniquement).",
    request=EntrepriseCreateSerializer,
    responses={
        201: EntrepriseSerializer,
        400: ErrorSerializer,
        401: ErrorSerializer,
        403: ErrorSerializer,
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def company_create(request):
    """
    POST /api/v1/companies
    Création d'une entreprise (admin cabinet).
    """
    # TODO: Vérifier rôle ADMIN_CABINET
    name = request.data.get("name")
    siret = request.data.get("siret")

    if not name or not siret:
        return Response(
            {"error": "name et siret requis"}, status=status.HTTP_400_BAD_REQUEST
        )

    if Entreprise.objects.filter(siret=siret).exists():
        return Response(
            {"error": "SIRET déjà existant"}, status=status.HTTP_400_BAD_REQUEST
        )

    company = Entreprise.objects.create(name=name, siret=siret)
    return Response(
        {
            "id": str(company.id),
            "name": company.name,
            "siret": company.siret,
            "is_active": company.is_active,
            "created_at": company.created_at.isoformat(),
        },
        status=status.HTTP_201_CREATED,
    )


@extend_schema(
    tags=["Companies"],
    summary="Détail d'une entreprise",
    description="Retourne les détails d'une entreprise.",
    responses={
        200: EntrepriseSerializer,
        401: ErrorSerializer,
        404: ErrorSerializer,
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def company_detail(request, company_id):
    """
    GET /api/v1/companies/{id}
    Détail d'une entreprise.
    """
    try:
        company = Entreprise.objects.get(id=company_id)
    except Entreprise.DoesNotExist:
        return Response(
            {"error": "Entreprise non trouvée"}, status=status.HTTP_404_NOT_FOUND
        )

    return Response(
        {
            "id": str(company.id),
            "name": company.name,
            "siret": company.siret,
            "is_active": company.is_active,
            "created_at": company.created_at.isoformat(),
        }
    )
