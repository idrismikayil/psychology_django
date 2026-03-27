from django.contrib import admin
from .models import TestInvitation


@admin.register(TestInvitation)
class TestInvitationAdmin(admin.ModelAdmin):
    list_display = ('sender_email', 'recipient_email', 'credit_count', 'is_shareable', 'status', 'created_at', 'expires_at')
    list_filter = ('status', 'created_at')
    search_fields = ('sender__email', 'recipient_email', 'token')
    readonly_fields = ('token', 'created_at', 'redeemed_at', 'revoked_at')

    def sender_email(self, obj):
        return obj.sender.email
    sender_email.short_description = "Sender"
