# Generated by Django 4.1.13 on 2024-03-28 08:23

from django.db import migrations


def remove_orphans(apps, schema_editor):
    CollectionField = apps.get_model("builder", "CollectionField")
    orphan_count, _ = CollectionField.objects.filter(tableelement=None).delete()
    print(f"\nDeleted {orphan_count}  orphan collection fields\n")


class Migration(migrations.Migration):
    dependencies = [
        ("builder", "0009_element_visibility"),
    ]

    operations = [
        migrations.RunPython(remove_orphans, reverse_code=migrations.RunPython.noop),
    ]
