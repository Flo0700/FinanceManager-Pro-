from django.db.models import Sum

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from apps.common.serializers import ErrorSerializer, MessageSerializer
from apps.invoices.models import Invoice

from .models import BankTransaction, Reconciliation
from .serializers import (
    BankTransactionCreateSerializer,
    BankTransactionSerializer,
    ReconciliationCreateSerializer,
    ReconciliationSerializer,
    TreasuryDashboardSerializer,
)


@extend_schema(
    tags=["Treasury"],
    summary="Dashboard trésorerie",
    description="Retourne le solde actuel, les totaux et les dernières transactions.",
    responses={
        200: TreasuryDashboardSerializer,
        401: ErrorSerializer,
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def treasury_dashboard(request):
    """
    GET /api/v1/treasury/dashboard
    Dashboard trésorerie.
    """
    entreprise = request.user.entreprise
    if not entreprise:
        return Response({"error": "Entreprise non définie"}, status=400)

    # Treasury balance from bank transactions
    transactions = BankTransaction.objects.filter(entreprise=entreprise)

    total_in = (
        transactions.filter(amount__gt=0).aggregate(total=Sum("amount"))["total"] or 0
    )
    total_out = (
        transactions.filter(amount__lt=0).aggregate(total=Sum("amount"))["total"] or 0
    )
    treasury_balance = total_in + total_out

    # Invoice statistics
    invoices = Invoice.objects.filter(entreprise=entreprise)
    total_invoices = invoices.count()
    total_amount_ttc = invoices.aggregate(total=Sum("total_ttc"))["total"] or 0
    pending_invoices = invoices.filter(status__in=["DRAFT", "ISSUED"]).count()
    pending_amount = (
        invoices.filter(status__in=["DRAFT", "ISSUED"]).aggregate(
            total=Sum("total_ttc")
        )["total"]
        or 0
    )

    # Recent transactions
    recent_transactions = transactions.order_by("-date", "-created_at")[:10]
    recent_transactions_data = [
        {
            "id": str(t.id),
            "date": t.date.isoformat(),
            "label": t.label,
            "amount": str(t.amount),
            "is_reconciled": Reconciliation.objects.filter(bank_transaction=t).exists(),
            "created_at": t.created_at.isoformat(),
        }
        for t in recent_transactions
    ]

    # Recent invoices
    recent_invoices = invoices.select_related("customer").order_by("-created_at")[:10]
    recent_invoices_data = [
        {
            "id": str(inv.id),
            "number": inv.number,
            "status": inv.status,
            "customer_name": inv.customer.name if inv.customer else "-",
            "issue_date": inv.issue_date.isoformat(),
            "due_date": inv.due_date.isoformat() if inv.due_date else None,
            "total_ttc": str(inv.total_ttc),
            "created_at": inv.created_at.isoformat(),
        }
        for inv in recent_invoices
    ]

    return Response(
        {
            "treasury_balance": float(treasury_balance),
            "total_in": float(total_in),
            "total_out": float(total_out),
            "total_invoices": total_invoices,
            "total_amount_ttc": float(total_amount_ttc),
            "pending_invoices": pending_invoices,
            "pending_amount": float(pending_amount),
            "recent_transactions": recent_transactions_data,
            "recent_invoices": recent_invoices_data,
        }
    )


@extend_schema(
    tags=["Treasury"],
    summary="Lister les transactions",
    description="Retourne la liste des transactions bancaires.",
    parameters=[
        OpenApiParameter(
            name="from_date", type=OpenApiTypes.DATE, description="Date début"
        ),
        OpenApiParameter(
            name="to_date", type=OpenApiTypes.DATE, description="Date fin"
        ),
    ],
    responses={
        200: BankTransactionSerializer(many=True),
        401: ErrorSerializer,
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def transaction_list(request):
    """
    GET /api/v1/bank-transactions
    Liste des transactions.
    """
    entreprise = request.user.entreprise
    if not entreprise:
        return Response({"error": "Entreprise non définie"}, status=400)

    transactions = BankTransaction.objects.filter(entreprise=entreprise)

    from_date = request.query_params.get("from_date")
    to_date = request.query_params.get("to_date")
    if from_date:
        transactions = transactions.filter(date__gte=from_date)
    if to_date:
        transactions = transactions.filter(date__lte=to_date)

    data = [
        {
            "id": str(t.id),
            "date": t.date.isoformat(),
            "label": t.label,
            "amount": str(t.amount),
            "created_at": t.created_at.isoformat(),
        }
        for t in transactions.order_by("-date")[:25]
    ]
    return Response(data)


@extend_schema(
    tags=["Treasury"],
    summary="Créer une transaction",
    description="Crée une nouvelle transaction bancaire.",
    request=BankTransactionCreateSerializer,
    responses={
        201: BankTransactionSerializer,
        400: ErrorSerializer,
        401: ErrorSerializer,
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def transaction_create(request):
    """
    POST /api/v1/bank-transactions
    Création d'une transaction.
    """
    entreprise = request.user.entreprise
    if not entreprise:
        return Response({"error": "Entreprise non définie"}, status=400)

    label = request.data.get("label")
    amount = request.data.get("amount")

    if not label or amount is None:
        return Response({"error": "label et amount requis"}, status=400)

    transaction = BankTransaction.objects.create(
        entreprise=entreprise,
        date=request.data.get("date"),
        label=label,
        amount=amount,
    )

    return Response(
        {
            "id": str(transaction.id),
            "date": transaction.date.isoformat(),
            "label": transaction.label,
            "amount": str(transaction.amount),
            "created_at": transaction.created_at.isoformat(),
        },
        status=201,
    )


# ========== Reconciliations ==========


@extend_schema(
    tags=["Treasury"],
    summary="Lister les rapprochements",
    description="Retourne la liste des rapprochements.",
    responses={
        200: ReconciliationSerializer(many=True),
        401: ErrorSerializer,
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def reconciliation_list(request):
    """
    GET /api/v1/reconciliations
    Liste des rapprochements.
    """
    entreprise = request.user.entreprise
    if not entreprise:
        return Response({"error": "Entreprise non définie"}, status=400)

    recos = Reconciliation.objects.filter(entreprise=entreprise).select_related(
        "invoice", "bank_transaction", "matched_by"
    )

    data = [
        {
            "id": str(r.id),
            "invoice_id": str(r.invoice_id),
            "invoice_number": r.invoice.number,
            "bank_transaction_id": str(r.bank_transaction_id),
            "transaction_label": r.bank_transaction.label,
            "matched_amount": str(r.matched_amount),
            "matched_at": r.matched_at.isoformat(),
            "matched_by_id": str(r.matched_by_id),
        }
        for r in recos.order_by("-matched_at")[:25]
    ]
    return Response(data)


@extend_schema(
    tags=["Treasury"],
    summary="Créer un rapprochement",
    description="Lie une transaction bancaire à une facture.",
    request=ReconciliationCreateSerializer,
    responses={
        201: ReconciliationSerializer,
        400: ErrorSerializer,
        401: ErrorSerializer,
        404: ErrorSerializer,
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reconciliation_create(request):
    """
    POST /api/v1/reconciliations
    Création d'un rapprochement.
    """
    entreprise = request.user.entreprise
    if not entreprise:
        return Response({"error": "Entreprise non définie"}, status=400)

    invoice_id = request.data.get("invoice_id")
    transaction_id = request.data.get("bank_transaction_id")
    matched_amount = request.data.get("matched_amount")

    if not all([invoice_id, transaction_id, matched_amount]):
        return Response(
            {"error": "invoice_id, bank_transaction_id et matched_amount requis"},
            status=400,
        )

    try:
        invoice = Invoice.objects.get(id=invoice_id, entreprise=entreprise)
    except Invoice.DoesNotExist:
        return Response({"error": "Facture non trouvée"}, status=404)

    try:
        transaction = BankTransaction.objects.get(
            id=transaction_id, entreprise=entreprise
        )
    except BankTransaction.DoesNotExist:
        return Response({"error": "Transaction non trouvée"}, status=404)

    reco = Reconciliation.objects.create(
        entreprise=entreprise,
        invoice=invoice,
        bank_transaction=transaction,
        matched_amount=matched_amount,
        matched_by=request.user,
    )

    return Response(
        {
            "id": str(reco.id),
            "invoice_id": str(reco.invoice_id),
            "bank_transaction_id": str(reco.bank_transaction_id),
            "matched_amount": str(reco.matched_amount),
            "matched_at": reco.matched_at.isoformat(),
            "matched_by_id": str(reco.matched_by_id),
        },
        status=201,
    )


@extend_schema(
    tags=["Treasury"],
    summary="Supprimer un rapprochement",
    description="Supprime un rapprochement existant.",
    responses={
        200: MessageSerializer,
        401: ErrorSerializer,
        404: ErrorSerializer,
    },
)
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def reconciliation_delete(request, reconciliation_id):
    """
    DELETE /api/v1/reconciliations/{id}
    Suppression d'un rapprochement.
    """
    entreprise = request.user.entreprise
    if not entreprise:
        return Response({"error": "Entreprise non définie"}, status=400)

    try:
        reco = Reconciliation.objects.get(id=reconciliation_id, entreprise=entreprise)
    except Reconciliation.DoesNotExist:
        return Response({"error": "Rapprochement non trouvé"}, status=404)

    reco.delete()
    return Response({"message": "Rapprochement supprimé"})
