import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.Model):
    """
    Rôles fixes et immuables du système.
    Créés uniquement via migration.
    """

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

    class Meta:
        db_table = "users_role"
        verbose_name = "Role"
        verbose_name_plural = "Roles"

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        if self.pk and Role.objects.filter(pk=self.pk).exists():
            raise RuntimeError("Roles are fixed and immutable (no updates allowed).")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise RuntimeError("Roles are fixed and cannot be deleted.")


class User(AbstractUser):
    """
    Utilisateur lié à Supabase.
    username = supabase sub (user ID)
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    username = models.CharField(max_length=255, unique=True)  # supabase sub
    email = models.EmailField(blank=True, default="")

    entreprise = models.ForeignKey(
        "companies.Entreprise",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="users",
    )

    role = models.ForeignKey(
        Role, on_delete=models.PROTECT, related_name="users", null=True, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "users_user"
        verbose_name = "User"
        verbose_name_plural = "Users"
        indexes = [
            models.Index(fields=["entreprise"]),
        ]

    def __str__(self):
        return self.email or self.username
