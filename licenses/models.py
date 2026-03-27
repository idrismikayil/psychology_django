import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class TestInvitation(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('REDEEMED', 'Redeemed'),
        ('REVOKED', 'Revoked'),
        ('EXPIRED', 'Expired'),
    )

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_invitations'
    )
    recipient_email = models.EmailField()
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='received_invitations'
    )
    credit_count = models.PositiveIntegerField(default=1)
    is_shareable = models.BooleanField(default=False)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    redeemed_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['sender', 'status']),
            models.Index(fields=['status', 'expires_at']),
        ]

    def __str__(self):
        return f"{self.sender.email} -> {self.recipient_email} x{self.credit_count} [{self.status}]"

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at and self.status == 'PENDING'

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)
