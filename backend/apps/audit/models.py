from django.db import models
import uuid


class AuditLog(models.Model):
    """Log d'audit pour tracer les actions critiques."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    entreprise = models.ForeignKey(
        'companies.Entreprise', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="audit_logs"
    )
    actor = models.ForeignKey(
        'users.User', 
        on_delete=models.PROTECT, 
        related_name="audit_logs"
    )

    action = models.CharField(max_length=64)
    entity_type = models.CharField(max_length=64, blank=True, default="")
    entity_id = models.CharField(max_length=64, blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_auditlog'
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        indexes = [
            models.Index(fields=["entreprise", "created_at"]),
            models.Index(fields=["actor", "created_at"]),
        ]

    def __str__(self):
        return f"{self.action} by {self.actor} at {self.created_at}"
