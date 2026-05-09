from django.db import migrations


def noop(apps, schema_editor):
    """Placeholder - template creation is now handled by ensure_default_templates management command"""
    pass


def reverse_noop(apps, schema_editor):
    """Placeholder for reverse migration"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('messaging', '0006_messagetemplate'),
    ]

    operations = [
        migrations.RunPython(noop, reverse_noop),
    ]
