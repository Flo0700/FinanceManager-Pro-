from django.db import migrations


def create_roles(apps, schema_editor):
    """Crée les rôles fixes du système."""
    Role = apps.get_model('core', 'Role')
    
    roles = [
        {
            'code': 'ADMIN_CABINET',
            'label': 'Administrateur Cabinet',
            'description': 'Administrateur du cabinet comptable avec accès complet',
        },
        {
            'code': 'GERANT_PME',
            'label': 'Gérant PME',
            'description': 'Gérant d\'une PME cliente (rôle par défaut)',
        },
        {
            'code': 'COMPTABLE_PME',
            'label': 'Comptable PME',
            'description': 'Comptable interne d\'une PME',
        },
        {
            'code': 'COLLABORATEUR',
            'label': 'Collaborateur',
            'description': 'Collaborateur avec accès limité',
        },
    ]
    
    for role_data in roles:
        Role.objects.get_or_create(
            code=role_data['code'],
            defaults={
                'label': role_data['label'],
                'description': role_data['description'],
            }
        )


def delete_roles(apps, schema_editor):
    """Supprime les rôles (pour rollback)."""
    Role = apps.get_model('core', 'Role')
    Role.objects.filter(code__in=[
        'ADMIN_CABINET', 'GERANT_PME', 'COMPTABLE_PME', 'COLLABORATEUR'
    ]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_roles, delete_roles),
    ]
