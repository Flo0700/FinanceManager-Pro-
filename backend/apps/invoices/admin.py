from django.contrib import admin

from .models import Customer, Invoice, InvoiceDocument, InvoiceLine


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "entreprise", "created_at")
    list_filter = ("entreprise",)
    search_fields = ("name", "email")
    readonly_fields = ("id", "created_at")


class InvoiceLineInline(admin.TabularInline):
    model = InvoiceLine
    extra = 0
    readonly_fields = ("id", "total_ht", "total_tva", "total_ttc")


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "number",
        "customer",
        "status",
        "total_ttc",
        "issue_date",
        "entreprise",
    )
    list_filter = ("status", "entreprise")
    search_fields = ("number", "customer__name")
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
        "hash_prev",
        "hash_curr",
        "locked_at",
    )
    inlines = [InvoiceLineInline]


@admin.register(InvoiceDocument)
class InvoiceDocumentAdmin(admin.ModelAdmin):
    list_display = ("invoice", "pdf_path", "generated_at")
    readonly_fields = ("id", "generated_at")
