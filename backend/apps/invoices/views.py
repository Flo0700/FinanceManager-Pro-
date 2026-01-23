from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from apps.common.serializers import ErrorSerializer, MessageSerializer

from .models import Customer, Invoice
from .serializers import (
    CustomerSerializer,
    InvoiceCreateSerializer,
    InvoiceListSerializer,
    InvoiceSerializer,
)


@extend_schema(
    tags=["Invoices"],
    summary="Lister les factures",
    description="Retourne la liste des factures de l'entreprise.",
    parameters=[
        OpenApiParameter(name="status", type=str, description="Filtrer par statut"),
        OpenApiParameter(
            name="from_date", type=OpenApiTypes.DATE, description="Date début"
        ),
        OpenApiParameter(
            name="to_date", type=OpenApiTypes.DATE, description="Date fin"
        ),
    ],
    responses={
        200: InvoiceListSerializer(many=True),
        401: ErrorSerializer,
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def invoice_list(request):
    """
    GET /api/v1/invoices
    Liste des factures (scopé entreprise).
    """
    # TODO: Filtrer par entreprise via X-Company-Id
    entreprise = request.user.entreprise
    if not entreprise:
        return Response({"error": "Entreprise non définie"}, status=400)

    invoices = Invoice.objects.filter(entreprise=entreprise).select_related("customer")

    # Filtres optionnels
    status_filter = request.query_params.get("status")
    if status_filter:
        invoices = invoices.filter(status=status_filter)

    data = [
        {
            "id": str(inv.id),
            "number": inv.number,
            "status": inv.status,
            "customer_name": inv.customer.name,
            "issue_date": inv.issue_date.isoformat(),
            "due_date": inv.due_date.isoformat() if inv.due_date else None,
            "total_ttc": str(inv.total_ttc),
            "created_at": inv.created_at.isoformat(),
        }
        for inv in invoices.order_by("-created_at")[:25]
    ]
    return Response(data)


@extend_schema(
    tags=["Invoices"],
    summary="Créer une facture",
    description="Crée une nouvelle facture en brouillon.",
    request=InvoiceCreateSerializer,
    responses={
        201: InvoiceSerializer,
        400: ErrorSerializer,
        401: ErrorSerializer,
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def invoice_create(request):
    """
    POST /api/v1/invoices
    Création d'une facture.
    """
    entreprise = request.user.entreprise
    if not entreprise:
        return Response({"error": "Entreprise non définie"}, status=400)

    customer_id = request.data.get("customer_id")
    if not customer_id:
        return Response({"error": "customer_id requis"}, status=400)

    try:
        customer = Customer.objects.get(id=customer_id, entreprise=entreprise)
    except Customer.DoesNotExist:
        return Response({"error": "Client non trouvé"}, status=404)

    # Générer numéro séquentiel
    last_invoice = (
        Invoice.objects.filter(entreprise=entreprise).order_by("-created_at").first()
    )
    if last_invoice and last_invoice.number:
        try:
            last_num = int(last_invoice.number.split("-")[-1])
            new_number = f"FAC-{last_num + 1:05d}"
        except ValueError:
            new_number = "FAC-00001"
    else:
        new_number = "FAC-00001"

    invoice = Invoice.objects.create(
        entreprise=entreprise,
        customer=customer,
        number=new_number,
        issue_date=request.data.get("issue_date"),
        due_date=request.data.get("due_date"),
    )

    return Response(
        {
            "id": str(invoice.id),
            "number": invoice.number,
            "status": invoice.status,
            "customer_id": str(customer.id),
            "issue_date": invoice.issue_date.isoformat(),
            "due_date": invoice.due_date.isoformat() if invoice.due_date else None,
            "total_ht": str(invoice.total_ht),
            "total_tva": str(invoice.total_tva),
            "total_ttc": str(invoice.total_ttc),
            "created_at": invoice.created_at.isoformat(),
        },
        status=201,
    )


@extend_schema(
    tags=["Invoices"],
    summary="Détail d'une facture",
    description="Retourne les détails d'une facture avec ses lignes.",
    responses={
        200: InvoiceSerializer,
        401: ErrorSerializer,
        404: ErrorSerializer,
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def invoice_detail(request, invoice_id):
    """
    GET /api/v1/invoices/{id}
    Détail d'une facture.
    """
    entreprise = request.user.entreprise
    if not entreprise:
        return Response({"error": "Entreprise non définie"}, status=400)

    try:
        invoice = (
            Invoice.objects.select_related("customer")
            .prefetch_related("lines")
            .get(id=invoice_id, entreprise=entreprise)
        )
    except Invoice.DoesNotExist:
        return Response({"error": "Facture non trouvée"}, status=404)

    lines = [
        {
            "id": str(line.id),
            "label": line.label,
            "qty": str(line.qty),
            "unit_price": str(line.unit_price),
            "vat_rate": str(line.vat_rate),
            "total_ht": str(line.total_ht),
            "total_tva": str(line.total_tva),
            "total_ttc": str(line.total_ttc),
        }
        for line in invoice.lines.all()
    ]

    return Response(
        {
            "id": str(invoice.id),
            "number": invoice.number,
            "status": invoice.status,
            "customer": {
                "id": str(invoice.customer.id),
                "name": invoice.customer.name,
                "email": invoice.customer.email,
            },
            "issue_date": invoice.issue_date.isoformat(),
            "due_date": invoice.due_date.isoformat() if invoice.due_date else None,
            "total_ht": str(invoice.total_ht),
            "total_tva": str(invoice.total_tva),
            "total_ttc": str(invoice.total_ttc),
            "lines": lines,
            "created_at": invoice.created_at.isoformat(),
            "updated_at": invoice.updated_at.isoformat(),
        }
    )


@extend_schema(
    tags=["Invoices"],
    summary="Valider une facture",
    description="Valide une facture (fige le numéro et le hash).",
    responses={
        200: MessageSerializer,
        400: ErrorSerializer,
        401: ErrorSerializer,
        404: ErrorSerializer,
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def invoice_validate(request, invoice_id):
    """
    POST /api/v1/invoices/{id}/validate
    Valide une facture.
    """
    entreprise = request.user.entreprise
    if not entreprise:
        return Response({"error": "Entreprise non définie"}, status=400)

    try:
        invoice = Invoice.objects.get(id=invoice_id, entreprise=entreprise)
    except Invoice.DoesNotExist:
        return Response({"error": "Facture non trouvée"}, status=404)

    if invoice.status != Invoice.Status.DRAFT:
        return Response(
            {"error": "Seules les factures en brouillon peuvent être validées"},
            status=400,
        )

    invoice.status = Invoice.Status.ISSUED
    invoice.save()

    return Response({"message": "Facture validée"})


@extend_schema(
    tags=["Invoices"],
    summary="Annuler une facture",
    description="Annule une facture (ne peut pas être supprimée).",
    responses={
        200: MessageSerializer,
        400: ErrorSerializer,
        401: ErrorSerializer,
        404: ErrorSerializer,
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def invoice_cancel(request, invoice_id):
    """
    POST /api/v1/invoices/{id}/cancel
    Annule une facture.
    """
    entreprise = request.user.entreprise
    if not entreprise:
        return Response({"error": "Entreprise non définie"}, status=400)

    try:
        invoice = Invoice.objects.get(id=invoice_id, entreprise=entreprise)
    except Invoice.DoesNotExist:
        return Response({"error": "Facture non trouvée"}, status=404)

    if invoice.status == Invoice.Status.CANCELED:
        return Response({"error": "Facture déjà annulée"}, status=400)

    invoice.status = Invoice.Status.CANCELED
    invoice.save()

    return Response({"message": "Facture annulée"})


# ========== Customers ==========


@extend_schema(
    tags=["Customers"],
    summary="Lister les clients",
    description="Retourne la liste des clients de l'entreprise.",
    responses={
        200: CustomerSerializer(many=True),
        401: ErrorSerializer,
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def customer_list(request):
    """
    GET /api/v1/customers
    Liste des clients.
    """
    entreprise = request.user.entreprise
    if not entreprise:
        return Response({"error": "Entreprise non définie"}, status=400)

    customers = Customer.objects.filter(entreprise=entreprise).order_by("name")
    data = [
        {
            "id": str(c.id),
            "name": c.name,
            "email": c.email,
            "phone": c.phone,
            "address": c.address,
            "vat_number": c.vat_number,
            "created_at": c.created_at.isoformat(),
        }
        for c in customers
    ]
    return Response(data)


@extend_schema(
    tags=["Customers"],
    summary="Créer un client",
    description="Crée un nouveau client.",
    request=CustomerSerializer,
    responses={
        201: CustomerSerializer,
        400: ErrorSerializer,
        401: ErrorSerializer,
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def customer_create(request):
    """
    POST /api/v1/customers
    Création d'un client.
    """
    entreprise = request.user.entreprise
    if not entreprise:
        return Response({"error": "Entreprise non définie"}, status=400)

    name = request.data.get("name")
    if not name:
        return Response({"error": "name requis"}, status=400)

    customer = Customer.objects.create(
        entreprise=entreprise,
        name=name,
        email=request.data.get("email", ""),
        phone=request.data.get("phone", ""),
        address=request.data.get("address", ""),
        vat_number=request.data.get("vat_number", ""),
    )

    return Response(
        {
            "id": str(customer.id),
            "name": customer.name,
            "email": customer.email,
            "phone": customer.phone,
            "address": customer.address,
            "vat_number": customer.vat_number,
            "created_at": customer.created_at.isoformat(),
        },
        status=201,
    )
