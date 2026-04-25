from django.db import models
from django.conf import settings


class NotificationLog(models.Model):
    """Audit trail for all outbound transactional emails."""
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notification_logs',
    )
    recipient_email = models.EmailField()
    subject = models.CharField(max_length=255)
    template_name = models.CharField(max_length=100)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='sent')
    error_message = models.TextField(blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f'{self.template_name} → {self.recipient_email} ({self.status})'
