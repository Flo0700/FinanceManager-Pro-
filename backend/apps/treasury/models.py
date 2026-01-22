import uuid

from django.db import models
from django.utils import timezone


class BankTransaction(models.Model):
    """Transaction bancaire."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    entreprise = models.ForeignKey(
        "companies.Entreprise",
        on_delete=models.CASCADE,
        related_name="bank_transactions",
    )
    date = models.DateField(default=timezone.now)
    label = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)  # + crédit / - débit
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "treasury_banktransaction"
        verbose_name = "Bank Transaction"
        verbose_name_plural = "Bank Transactions"
        indexes = [models.Index(fields=["entreprise", "date"])]

    def __str__(self):
        return f"{self.date} - {self.label} ({self.amount})"


class Reconciliation(models.Model):
    """Rapprochement entre facture et transaction bancaire."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    entreprise = models.ForeignKey(
        "companies.Entreprise", on_delete=models.CASCADE, related_name="reconciliations"
    )

    invoice = models.ForeignKey(
        "invoices.Invoice", on_delete=models.PROTECT, related_name="reconciliations"
    )
    bank_transaction = models.ForeignKey(
        BankTransaction, on_delete=models.PROTECT, related_name="reconciliations"
    )

    matched_amount = models.DecimalField(max_digits=12, decimal_places=2)
    matched_at = models.DateTimeField(auto_now_add=True)

    matched_by = models.ForeignKey(
        "users.User", on_delete=models.PROTECT, related_name="reconciliations"
    )

    class Meta:
        db_table = "treasury_reconciliation"
        verbose_name = "Reconciliation"
        verbose_name_plural = "Reconciliations"
        constraints = [
            models.UniqueConstraint(
                fields=["entreprise", "invoice", "bank_transaction"],
                name="uniq_reco_per_tenant_invoice_tx",
            )
        ]
        indexes = [models.Index(fields=["entreprise", "matched_at"])]

    def __str__(self):
        return f"Reco: {self.invoice} <-> {self.bank_transaction}"
