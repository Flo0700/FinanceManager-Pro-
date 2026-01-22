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


class Membership(models.Model):
    """
    Liaison entre un utilisateur et une entreprise (tenant) avec un rôle.
    Permet le multi-tenant : un utilisateur peut appartenir à plusieurs entreprises.
    """

    # Rôles pour le membership (différent des rôles système)
    ROLE_TENANT_OWNER = "TENANT_OWNER"
    ROLE_COMPTABLE = "COMPTABLE"
    ROLE_COLLABORATEUR = "COLLABORATEUR"
    ROLE_ADMIN_CABINET = "ADMIN_CABINET"

    ROLE_CHOICES = [
        (ROLE_TENANT_OWNER, "Gérant (Propriétaire)"),
        (ROLE_COMPTABLE, "Comptable"),
        (ROLE_COLLABORATEUR, "Collaborateur"),
        (ROLE_ADMIN_CABINET, "Admin Cabinet"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    entreprise = models.ForeignKey(
        "companies.Entreprise",
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    role = models.CharField(
        max_length=50,
        choices=ROLE_CHOICES,
        default=ROLE_COLLABORATEUR,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "users_membership"
        verbose_name = "Membership"
        verbose_name_plural = "Memberships"
        # Un utilisateur ne peut avoir qu'un seul membership par entreprise
        constraints = [
            models.UniqueConstraint(
                fields=["user", "entreprise"],
                name="unique_user_entreprise_membership",
            )
        ]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["entreprise"]),
            models.Index(fields=["role"]),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.entreprise.name} ({self.role})"
