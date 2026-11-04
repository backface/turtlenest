from django.db import migrations


def unpublish_private(apps, schema_editor):
    Project = apps.get_model("projects", "Project")
    Project.objects.filter(is_public=False, is_published=True).update(is_published=False)


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0008_alter_project_is_published"),
    ]

    operations = [
        migrations.RunPython(unpublish_private, migrations.RunPython.noop),
    ]
