from django.contrib import admin

from .models import Entreprise


@admin.register(Entreprise)
class EntrepriseAdmin(admin.ModelAdmin):
    list_display = ("name", "siret", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "siret")
    readonly_fields = ("id", "created_at")
