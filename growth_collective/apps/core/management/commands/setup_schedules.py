"""
Management command to register all django-q2 scheduled tasks.
Run once after deployment: python manage.py setup_schedules
Safe to re-run — uses get_or_create so it won't duplicate schedules.
"""
from django.core.management.base import BaseCommand
from django_q.models import Schedule


SCHEDULES = [
    {
        'name': 'Booking reminders (24h)',
        'func': 'apps.bookings.tasks.send_booking_reminders',
        'schedule_type': Schedule.HOURLY,
    },
    {
        'name': 'Event reminders (24h)',
        'func': 'apps.events.tasks.send_event_reminders',
        'schedule_type': Schedule.HOURLY,
    },
    {
        'name': 'Expire old offers',
        'func': 'apps.offers.tasks.expire_old_offers',
        'schedule_type': Schedule.HOURLY,
    },
    {
        'name': 'Reset monthly points',
        'func': 'apps.points.tasks.reset_monthly_points',
        'schedule_type': Schedule.MONTHLY,
    },
]


class Command(BaseCommand):
    help = 'Register all django-q2 scheduled tasks. Safe to re-run.'

    def handle(self, *args, **options):
        created_count = 0
        for schedule in SCHEDULES:
            _, created = Schedule.objects.get_or_create(
                func=schedule['func'],
                defaults={
                    'name': schedule['name'],
                    'schedule_type': schedule['schedule_type'],
                },
            )
            status = 'created' if created else 'already exists'
            self.stdout.write(f'  {schedule["name"]}: {status}')
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. {created_count} new schedule(s) registered.'
        ))
