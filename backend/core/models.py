from django.db import models
import uuid
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

# Create your models here.

class Entreprise(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=255)
    siret = models.CharField(max_length=14, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.siret})"


# =========================
# Roles (FIXES & immuables)
# =========================

class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Codes fixes (utilisés dans le code)
    ADMIN_CABINET = "ADMIN_CABINET"
    GERANT_PME = "GERANT_PME"
    COMPTABLE_PME = "COMPTABLE_PME"
    COLLABORATEUR = "COLLABORATEUR"

    code = models.CharField(max_length=50, unique=True)
    label = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    # Immutabilité: interdit UPDATE/DELETE (on ne crée que via migration)
    def save(self, *args, **kwargs):
        if self.pk and Role.objects.filter(pk=self.pk).exists():
            raise RuntimeError("Roles are fixed and immutable (no updates allowed).")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise RuntimeError("Roles are fixed and cannot be deleted.")

    def __str__(self):
        return self.code


# =========================
# User (lié Supabase)
# username = supabase sub
# =========================
class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    username = models.CharField(max_length=255, unique=True)  # supabase sub
    email = models.EmailField(blank=True, default="")

    entreprise = models.ForeignKey(
        Entreprise,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="users",
    )

    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        related_name="users",
        null=True,   # on le rendra non-null après init rôles + bootstrap
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["entreprise"]),
        ]


# =========================
# Facturation
# =========================
class Customer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    entreprise = models.ForeignKey(
        Entreprise, on_delete=models.CASCADE, related_name="customers"
    )
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, default="")
    phone = models.CharField(max_length=30, blank=True, default="")
    address = models.TextField(blank=True, default="")
    vat_number = models.CharField(max_length=32, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["entreprise", "name"])]

    def __str__(self):
        return self.name


class Invoice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Status(models.TextChoices):
        DRAFT = "DRAFT"
        ISSUED = "ISSUED"
        PAID = "PAID"
        CANCELED = "CANCELED"

    entreprise = models.ForeignKey(
        Entreprise, on_delete=models.CASCADE, related_name="invoices"
    )
    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT, related_name="invoices"
    )

    number = models.CharField(max_length=50)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)

    issue_date = models.DateField(default=timezone.now)
    due_date = models.DateField(null=True, blank=True)

    total_ht = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_tva = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_ttc = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Anti-fraude MVP (chaînage + verrouillage)
    hash_prev = models.CharField(max_length=64, null=True, blank=True)
    hash_curr = models.CharField(max_length=64, null=True, blank=True)
    locked_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["entreprise", "number"], name="uniq_invoice_number_per_tenant"),
        ]
        indexes = [
            models.Index(fields=["entreprise", "issue_date"]),
            models.Index(fields=["entreprise", "status"]),
        ]


class InvoiceLine(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    entreprise = models.ForeignKey(
        Entreprise, on_delete=models.CASCADE, related_name="invoice_lines"
    )
    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name="lines"
    )

    label = models.CharField(max_length=255)
    qty = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=20)

    total_ht = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_tva = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_ttc = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        indexes = [models.Index(fields=["entreprise", "invoice"])]


# Document PDF généré
class InvoiceDocument(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    entreprise = models.ForeignKey(
        Entreprise, on_delete=models.CASCADE, related_name="invoice_documents"
    )
    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name="documents"
    )
    pdf_path = models.CharField(max_length=500)
    generated_at = models.DateTimeField(auto_now_add=True)


# =========================
# Trésorerie
# =========================
class BankTransaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    entreprise = models.ForeignKey(
        Entreprise, on_delete=models.CASCADE, related_name="bank_transactions"
    )
    date = models.DateField(default=timezone.now)
    label = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)  # + crédit / - débit
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["entreprise", "date"])]


class Reconciliation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    entreprise = models.ForeignKey(
        Entreprise, on_delete=models.CASCADE, related_name="reconciliations"
    )

    invoice = models.ForeignKey(
        Invoice, on_delete=models.PROTECT, related_name="reconciliations"
    )
    bank_transaction = models.ForeignKey(
        BankTransaction, on_delete=models.PROTECT, related_name="reconciliations"
    )

    matched_amount = models.DecimalField(max_digits=12, decimal_places=2)
    matched_at = models.DateTimeField(auto_now_add=True)

    matched_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="reconciliations"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["entreprise", "invoice", "bank_transaction"],
                name="uniq_reco_per_tenant_invoice_tx",
            )
        ]
        indexes = [models.Index(fields=["entreprise", "matched_at"])]


# =========================
# Audit minimal
# =========================

class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    entreprise = models.ForeignKey(
        Entreprise, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs"
    )
    actor = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="audit_logs"
    )

    action = models.CharField(max_length=64)
    entity_type = models.CharField(max_length=64, blank=True, default="")
    entity_id = models.CharField(max_length=64, blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["entreprise", "created_at"]),
            models.Index(fields=["actor", "created_at"]),
        ]
