from django.db import migrations


def create_social_links_room(apps, schema_editor):
    Room = apps.get_model('chat', 'Room')
    Room.objects.get_or_create(
        slug='social-links',
        defaults={
            'room_type': 'community',
            'name': 'Social Links',
            'requires_premium': True,
            'is_active': True,
        }
    )


class Migration(migrations.Migration):
    dependencies = [('chat', '0003_room_participants')]
    operations = [migrations.RunPython(create_social_links_room, migrations.RunPython.noop)]
