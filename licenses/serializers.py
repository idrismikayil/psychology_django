from rest_framework import serializers
from django.db.models import Sum
from .models import TestInvitation


class CreateInvitationSerializer(serializers.Serializer):
    recipient_email = serializers.EmailField()
    credit_count = serializers.IntegerField(
        required=False, default=1, min_value=1
    )
    is_shareable = serializers.BooleanField(required=False, default=False)
    expires_in_days = serializers.IntegerField(
        required=False, default=7, min_value=1, max_value=30
    )

    def validate_recipient_email(self, value):
        user = self.context['request'].user
        if value.lower() == user.email.lower():
            raise serializers.ValidationError("You cannot send an invitation to yourself.")
        return value.lower()

    def validate(self, data):
        user = self.context['request'].user
        reserved = TestInvitation.objects.filter(
            sender=user, status='PENDING'
        ).aggregate(total=Sum('credit_count'))['total'] or 0
        available = user.active_test_count - reserved
        requested = data.get('credit_count', 1)
        if requested > available:
            raise serializers.ValidationError(
                f"You only have {available} available test credit(s) to send."
            )
        return data


class InvitationListSerializer(serializers.ModelSerializer):
    is_expired = serializers.BooleanField(read_only=True)
    redeemed_by_email = serializers.SerializerMethodField()

    class Meta:
        model = TestInvitation
        fields = [
            'id', 'recipient_email', 'credit_count', 'is_shareable',
            'status', 'token', 'created_at', 'expires_at',
            'redeemed_at', 'is_expired', 'redeemed_by_email'
        ]
        read_only_fields = fields

    def get_redeemed_by_email(self, obj):
        if obj.recipient:
            return obj.recipient.email
        return None


class InvitationDetailSerializer(serializers.ModelSerializer):
    sender_email = serializers.EmailField(source='sender.email', read_only=True)

    class Meta:
        model = TestInvitation
        fields = [
            'id', 'sender_email', 'recipient_email', 'credit_count',
            'is_shareable', 'status', 'expires_at'
        ]
