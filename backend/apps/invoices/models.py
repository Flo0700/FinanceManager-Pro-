import uuid

from django.db import models
from django.utils import timezone


class Customer(models.Model):
    """Client d'une entreprise."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    entreprise = models.ForeignKey(
        "companies.Entreprise", on_delete=models.CASCADE, related_name="customers"
    )
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, default="")
    phone = models.CharField(max_length=30, blank=True, default="")
    address = models.TextField(blank=True, default="")
    vat_number = models.CharField(max_length=32, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "invoices_customer"
        verbose_name = "Customer"
        verbose_name_plural = "Customers"
        indexes = [models.Index(fields=["entreprise", "name"])]

    def __str__(self):
        return self.name


class Invoice(models.Model):
    """Facture."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Brouillon"
        ISSUED = "ISSUED", "Émise"
        PAID = "PAID", "Payée"
        CANCELED = "CANCELED", "Annulée"

    entreprise = models.ForeignKey(
        "companies.Entreprise", on_delete=models.CASCADE, related_name="invoices"
    )
    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT, related_name="invoices"
    )

    number = models.CharField(max_length=50)
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.DRAFT
    )

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
        db_table = "invoices_invoice"
        verbose_name = "Invoice"
        verbose_name_plural = "Invoices"
        constraints = [
            models.UniqueConstraint(
                fields=["entreprise", "number"], name="uniq_invoice_number_per_tenant"
            ),
        ]
        indexes = [
            models.Index(fields=["entreprise", "issue_date"]),
            models.Index(fields=["entreprise", "status"]),
        ]

    def __str__(self):
        return f"Facture {self.number}"


class InvoiceLine(models.Model):
    """Ligne de facture."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    entreprise = models.ForeignKey(
        "companies.Entreprise", on_delete=models.CASCADE, related_name="invoice_lines"
    )
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="lines")

    label = models.CharField(max_length=255)
    qty = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=20)

    total_ht = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_tva = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_ttc = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = "invoices_invoiceline"
        verbose_name = "Invoice Line"
        verbose_name_plural = "Invoice Lines"
        indexes = [models.Index(fields=["entreprise", "invoice"])]

    def __str__(self):
        return f"{self.label} x{self.qty}"


class InvoiceDocument(models.Model):
    """Document PDF généré pour une facture."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    entreprise = models.ForeignKey(
        "companies.Entreprise",
        on_delete=models.CASCADE,
        related_name="invoice_documents",
    )
    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name="documents"
    )
    pdf_path = models.CharField(max_length=500)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "invoices_invoicedocument"
        verbose_name = "Invoice Document"
        verbose_name_plural = "Invoice Documents"

    def __str__(self):
        return f"Document {self.invoice.number}"
