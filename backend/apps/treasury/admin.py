from django.contrib import admin
from .models import BankTransaction, Reconciliation


@admin.register(BankTransaction)
class BankTransactionAdmin(admin.ModelAdmin):
    list_display = ('date', 'label', 'amount', 'entreprise', 'created_at')
    list_filter = ('entreprise', 'date')
    search_fields = ('label',)
    readonly_fields = ('id', 'created_at')


@admin.register(Reconciliation)
class ReconciliationAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'bank_transaction', 'matched_amount', 'matched_by', 'matched_at')
    list_filter = ('entreprise',)
    readonly_fields = ('id', 'matched_at')
