import uuid

from django.db import models


class Entreprise(models.Model):
    """
    Entreprise (PME) - Tenant principal pour l'isolation multi-tenant.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=255)
    siret = models.CharField(max_length=14, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "companies_entreprise"
        verbose_name = "Entreprise"
        verbose_name_plural = "Entreprises"
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.siret})"
