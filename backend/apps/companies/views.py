from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema

from apps.common.serializers import ErrorSerializer
from apps.users.models import Membership

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
    description="Crée une nouvelle entreprise et assigne l'utilisateur comme TENANT_OWNER.",
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
    POST /api/v1/companies/create
    Création d'une entreprise avec membership TENANT_OWNER.
    """
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

    # Créer l'entreprise
    company = Entreprise.objects.create(name=name, siret=siret)

    # Créer le membership avec rôle TENANT_OWNER
    membership = Membership.objects.create(
        user=request.user,
        entreprise=company,
        role=Membership.ROLE_TENANT_OWNER,
    )

    # Définir cette entreprise comme tenant actif de l'utilisateur
    request.user.entreprise = company
    request.user.save(update_fields=["entreprise"])

    return Response(
        {
            "id": str(company.id),
            "name": company.name,
            "siret": company.siret,
            "is_active": company.is_active,
            "created_at": company.created_at.isoformat(),
            "membership": {
                "id": str(membership.id),
                "role": membership.role,
            },
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


# ============================================
# Endpoints Tenants (Multi-tenant)
# ============================================


@extend_schema(
    tags=["Tenants"],
    summary="Liste des entreprises de l'utilisateur",
    description="Retourne la liste des entreprises auxquelles l'utilisateur a accès via ses memberships.",
    responses={
        200: {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string", "format": "uuid"},
                    "name": {"type": "string"},
                    "siret": {"type": "string"},
                    "role": {"type": "string"},
                    "is_active": {"type": "boolean"},
                },
            },
        },
        401: ErrorSerializer,
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def tenant_list(request):
    """
    GET /api/v1/tenants
    Liste des entreprises accessibles par l'utilisateur.
    """
    memberships = Membership.objects.filter(
        user=request.user, is_active=True
    ).select_related("entreprise")

    data = [
        {
            "id": str(m.entreprise.id),
            "name": m.entreprise.name,
            "siret": m.entreprise.siret,
            "role": m.role,
            "is_active": m.entreprise.is_active,
            "membership_id": str(m.id),
            "joined_at": m.created_at.isoformat(),
        }
        for m in memberships
        if m.entreprise.is_active
    ]
    return Response(data)


@extend_schema(
    tags=["Tenants"],
    summary="Changer de tenant actif",
    description="Définit l'entreprise active pour l'utilisateur connecté.",
    request={
        "type": "object",
        "properties": {
            "tenant_id": {"type": "string", "format": "uuid"},
        },
        "required": ["tenant_id"],
    },
    responses={
        200: {
            "type": "object",
            "properties": {
                "message": {"type": "string"},
                "tenant": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "role": {"type": "string"},
                    },
                },
            },
        },
        400: ErrorSerializer,
        401: ErrorSerializer,
        403: ErrorSerializer,
        404: ErrorSerializer,
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def tenant_switch(request):
    """
    POST /api/v1/tenants/switch
    Change le tenant actif de l'utilisateur.
    """
    tenant_id = request.data.get("tenant_id")

    if not tenant_id:
        return Response(
            {"error": "tenant_id requis"}, status=status.HTTP_400_BAD_REQUEST
        )

    # Vérifier que l'utilisateur a accès à ce tenant
    try:
        membership = Membership.objects.select_related("entreprise").get(
            user=request.user, entreprise_id=tenant_id, is_active=True
        )
    except Membership.DoesNotExist:
        return Response(
            {"error": "Accès non autorisé à cette entreprise"},
            status=status.HTTP_403_FORBIDDEN,
        )

    if not membership.entreprise.is_active:
        return Response(
            {"error": "Cette entreprise n'est plus active"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Mettre à jour l'entreprise active de l'utilisateur
    request.user.entreprise = membership.entreprise
    request.user.save(update_fields=["entreprise"])

    return Response(
        {
            "message": "Tenant actif changé",
            "tenant": {
                "id": str(membership.entreprise.id),
                "name": membership.entreprise.name,
                "siret": membership.entreprise.siret,
                "role": membership.role,
            },
        },
        status=status.HTTP_200_OK,
    )


@extend_schema(
    tags=["Tenants"],
    summary="Détails du tenant actif",
    description="Retourne les détails du tenant actuellement actif pour l'utilisateur.",
    responses={
        200: {
            "type": "object",
            "properties": {
                "id": {"type": "string", "format": "uuid"},
                "name": {"type": "string"},
                "siret": {"type": "string"},
                "role": {"type": "string"},
                "is_active": {"type": "boolean"},
            },
        },
        401: ErrorSerializer,
        404: ErrorSerializer,
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def tenant_current(request):
    """
    GET /api/v1/tenants/current
    Retourne le tenant actuellement actif.
    """
    if not request.user.entreprise:
        return Response(
            {"error": "Aucun tenant actif. Créez ou sélectionnez une entreprise."},
            status=status.HTTP_404_NOT_FOUND,
        )

    entreprise = request.user.entreprise

    # Récupérer le rôle via membership
    try:
        membership = Membership.objects.get(
            user=request.user, entreprise=entreprise, is_active=True
        )
        role = membership.role
    except Membership.DoesNotExist:
        role = None

    return Response(
        {
            "id": str(entreprise.id),
            "name": entreprise.name,
            "siret": entreprise.siret,
            "role": role,
            "is_active": entreprise.is_active,
        }
    )


# ============================================
# Endpoints Team (Gestion des membres)
# ============================================


@extend_schema(
    tags=["Team"],
    summary="Liste des membres de l'équipe",
    description="Retourne la liste des membres de l'entreprise active.",
    responses={
        200: {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string", "format": "uuid"},
                    "user_id": {"type": "string", "format": "uuid"},
                    "email": {"type": "string"},
                    "role": {"type": "string"},
                    "is_active": {"type": "boolean"},
                    "joined_at": {"type": "string", "format": "date-time"},
                },
            },
        },
        401: ErrorSerializer,
        404: ErrorSerializer,
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def team_members_list(request):
    """
    GET /api/v1/tenants/members
    Liste des membres de l'entreprise active.
    """
    if not request.user.entreprise:
        return Response(
            {"error": "Aucun tenant actif"}, status=status.HTTP_404_NOT_FOUND
        )

    memberships = Membership.objects.filter(
        entreprise=request.user.entreprise, is_active=True
    ).select_related("user")

    data = [
        {
            "id": str(m.id),
            "user_id": str(m.user.id),
            "email": m.user.email,
            "role": m.role,
            "is_active": m.is_active,
            "joined_at": m.created_at.isoformat(),
        }
        for m in memberships
    ]
    return Response(data)


@extend_schema(
    tags=["Team"],
    summary="Inviter un membre",
    description="Invite un utilisateur existant à rejoindre l'entreprise.",
    request={
        "type": "object",
        "properties": {
            "email": {"type": "string", "format": "email"},
            "role": {"type": "string", "enum": ["COMPTABLE", "COLLABORATEUR"]},
        },
        "required": ["email", "role"],
    },
    responses={
        201: {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "email": {"type": "string"},
                "role": {"type": "string"},
                "message": {"type": "string"},
            },
        },
        400: ErrorSerializer,
        401: ErrorSerializer,
        403: ErrorSerializer,
        404: ErrorSerializer,
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def team_member_invite(request):
    """
    POST /api/v1/tenants/members/invite
    Invite un utilisateur à rejoindre l'entreprise.
    """
    from apps.users.models import User

    if not request.user.entreprise:
        return Response(
            {"error": "Aucun tenant actif"}, status=status.HTTP_404_NOT_FOUND
        )

    # Vérifier que l'utilisateur courant a les droits (TENANT_OWNER ou ADMIN)
    try:
        current_membership = Membership.objects.get(
            user=request.user, entreprise=request.user.entreprise, is_active=True
        )
        if current_membership.role not in [
            Membership.ROLE_TENANT_OWNER,
            Membership.ROLE_ADMIN_CABINET,
        ]:
            return Response(
                {"error": "Vous n'avez pas les droits pour inviter des membres"},
                status=status.HTTP_403_FORBIDDEN,
            )
    except Membership.DoesNotExist:
        return Response(
            {"error": "Accès non autorisé"}, status=status.HTTP_403_FORBIDDEN
        )

    email = request.data.get("email")
    role = request.data.get("role", Membership.ROLE_COLLABORATEUR)

    if not email:
        return Response({"error": "Email requis"}, status=status.HTTP_400_BAD_REQUEST)

    # Valider le rôle
    valid_roles = [Membership.ROLE_COMPTABLE, Membership.ROLE_COLLABORATEUR]
    if role not in valid_roles:
        return Response(
            {"error": f"Rôle invalide. Choix: {', '.join(valid_roles)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Vérifier si l'utilisateur existe
    try:
        user_to_invite = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response(
            {"error": "Utilisateur non trouvé. Il doit d'abord créer un compte."},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Vérifier si le membre existe déjà
    if Membership.objects.filter(
        user=user_to_invite, entreprise=request.user.entreprise
    ).exists():
        return Response(
            {"error": "Cet utilisateur est déjà membre de l'entreprise"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Créer le membership
    membership = Membership.objects.create(
        user=user_to_invite,
        entreprise=request.user.entreprise,
        role=role,
    )

    return Response(
        {
            "id": str(membership.id),
            "email": user_to_invite.email,
            "role": membership.role,
            "message": f"Utilisateur {email} ajouté avec succès",
        },
        status=status.HTTP_201_CREATED,
    )


@extend_schema(
    tags=["Team"],
    summary="Retirer un membre",
    description="Retire un membre de l'entreprise.",
    responses={
        200: {"type": "object", "properties": {"message": {"type": "string"}}},
        400: ErrorSerializer,
        401: ErrorSerializer,
        403: ErrorSerializer,
        404: ErrorSerializer,
    },
)
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def team_member_remove(request, membership_id):
    """
    DELETE /api/v1/tenants/members/{membership_id}
    Retire un membre de l'entreprise.
    """
    if not request.user.entreprise:
        return Response(
            {"error": "Aucun tenant actif"}, status=status.HTTP_404_NOT_FOUND
        )

    # Vérifier que l'utilisateur courant a les droits
    try:
        current_membership = Membership.objects.get(
            user=request.user, entreprise=request.user.entreprise, is_active=True
        )
        if current_membership.role not in [
            Membership.ROLE_TENANT_OWNER,
            Membership.ROLE_ADMIN_CABINET,
        ]:
            return Response(
                {"error": "Vous n'avez pas les droits pour retirer des membres"},
                status=status.HTTP_403_FORBIDDEN,
            )
    except Membership.DoesNotExist:
        return Response(
            {"error": "Accès non autorisé"}, status=status.HTTP_403_FORBIDDEN
        )

    # Trouver le membership à supprimer
    try:
        membership = Membership.objects.get(
            id=membership_id, entreprise=request.user.entreprise
        )
    except Membership.DoesNotExist:
        return Response(
            {"error": "Membre non trouvé"}, status=status.HTTP_404_NOT_FOUND
        )

    # Empêcher de se retirer soi-même
    if membership.user == request.user:
        return Response(
            {"error": "Vous ne pouvez pas vous retirer vous-même"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Empêcher de retirer le propriétaire
    if membership.role == Membership.ROLE_TENANT_OWNER:
        return Response(
            {"error": "Impossible de retirer le propriétaire de l'entreprise"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Désactiver le membership (soft delete)
    membership.is_active = False
    membership.save(update_fields=["is_active", "updated_at"])

    return Response({"message": "Membre retiré avec succès"})


@extend_schema(
    tags=["Team"],
    summary="Modifier le rôle d'un membre",
    description="Modifie le rôle d'un membre de l'entreprise.",
    request={
        "type": "object",
        "properties": {
            "role": {"type": "string", "enum": ["COMPTABLE", "COLLABORATEUR"]},
        },
        "required": ["role"],
    },
    responses={
        200: {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "role": {"type": "string"},
                "message": {"type": "string"},
            },
        },
        400: ErrorSerializer,
        401: ErrorSerializer,
        403: ErrorSerializer,
        404: ErrorSerializer,
    },
)
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def team_member_update(request, membership_id):
    """
    PATCH /api/v1/tenants/members/{membership_id}
    Modifie le rôle d'un membre.
    """
    if not request.user.entreprise:
        return Response(
            {"error": "Aucun tenant actif"}, status=status.HTTP_404_NOT_FOUND
        )

    # Vérifier que l'utilisateur courant a les droits
    try:
        current_membership = Membership.objects.get(
            user=request.user, entreprise=request.user.entreprise, is_active=True
        )
        if current_membership.role not in [
            Membership.ROLE_TENANT_OWNER,
            Membership.ROLE_ADMIN_CABINET,
        ]:
            return Response(
                {"error": "Vous n'avez pas les droits pour modifier les rôles"},
                status=status.HTTP_403_FORBIDDEN,
            )
    except Membership.DoesNotExist:
        return Response(
            {"error": "Accès non autorisé"}, status=status.HTTP_403_FORBIDDEN
        )

    # Trouver le membership à modifier
    try:
        membership = Membership.objects.get(
            id=membership_id, entreprise=request.user.entreprise, is_active=True
        )
    except Membership.DoesNotExist:
        return Response(
            {"error": "Membre non trouvé"}, status=status.HTTP_404_NOT_FOUND
        )

    # Empêcher de modifier le propriétaire
    if membership.role == Membership.ROLE_TENANT_OWNER:
        return Response(
            {"error": "Impossible de modifier le rôle du propriétaire"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    role = request.data.get("role")
    valid_roles = [Membership.ROLE_COMPTABLE, Membership.ROLE_COLLABORATEUR]
    if role not in valid_roles:
        return Response(
            {"error": f"Rôle invalide. Choix: {', '.join(valid_roles)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    membership.role = role
    membership.save(update_fields=["role", "updated_at"])

    return Response(
        {
            "id": str(membership.id),
            "role": membership.role,
            "message": "Rôle mis à jour avec succès",
        }
    )
