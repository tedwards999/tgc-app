from django.db import migrations


def create_community_room(apps, schema_editor):
    Room = apps.get_model('chat', 'Room')
    Room.objects.get_or_create(
        slug='community',
        defaults={
            'room_type': 'community',
            'name': 'Community Lobby',
            'requires_premium': False,
            'is_active': True,
        }
    )


class Migration(migrations.Migration):
    dependencies = [('chat', '0001_initial')]
    operations = [migrations.RunPython(create_community_room, migrations.RunPython.noop)]
