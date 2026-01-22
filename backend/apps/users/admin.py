from django.contrib import admin

from .models import Role, User


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("code", "label", "created_at")
    search_fields = ("code", "label")
    readonly_fields = ("id", "code", "label", "description", "created_at")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "username",
        "role",
        "entreprise",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active", "role", "entreprise")
    search_fields = ("email", "username")
    readonly_fields = ("id", "username", "created_at")
