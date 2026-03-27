from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import F, Sum
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from authApp.models import CustomUser
from .models import TestInvitation
from .serializers import (
    CreateInvitationSerializer,
    InvitationDetailSerializer,
    InvitationListSerializer,
)


class SendInvitationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateInvitationSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        expires_in_days = serializer.validated_data.get('expires_in_days', 7)
        credit_count = serializer.validated_data.get('credit_count', 1)
        is_shareable = serializer.validated_data.get('is_shareable', False)
        invitation = TestInvitation.objects.create(
            sender=request.user,
            recipient_email=serializer.validated_data['recipient_email'],
            credit_count=credit_count,
            is_shareable=is_shareable,
            expires_at=timezone.now() + timedelta(days=expires_in_days),
        )

        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
        redeem_url = f"{frontend_url}/redeem/{invitation.token}"

        sender_name = request.user.get_full_name() or request.user.email
        expires_str = invitation.expires_at.strftime('%d.%m.%Y')

        subject = f"{sender_name} sizinlə şəxsiyyət testi paylaşdı"

        # Plain text fallback
        message = (
            f"Salam,\n\n"
            f"{sender_name} ({request.user.email}) Octopus platformasında sizinlə "
            f"{credit_count} şəxsiyyət testi paylaşdı.\n\n"
            f"Qəbul etmək üçün aşağıdakı linkə daxil olun:\n"
            f"{redeem_url}\n\n"
            f"Detallar:\n"
            f"- Göndərən: {sender_name}\n"
            f"- Test sayı: {credit_count}\n"
            f"- Etibarlıdır: {expires_str} tarixinə qədər\n\n"
            f"Bu emaili gözləmirdinizsə, onu nəzərə almaya bilərsiniz.\n\n"
            f"Hörmətlə,\n"
            f"Octopus komandası\n"
            f"https://octopus.com.az\n"
        )

        # HTML email
        html_message = f"""<!DOCTYPE html>
<html lang="az">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{subject}</title>
</head>
<body style="margin:0; padding:0; background-color:#f5f5f5; font-family: Arial, Helvetica, sans-serif; color:#333333;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color:#f5f5f5;">
    <tr>
      <td align="center" style="padding:30px 15px;">
        <table role="presentation" width="560" cellspacing="0" cellpadding="0" border="0" style="max-width:560px; width:100%; background-color:#ffffff; border:1px solid #e0e0e0; border-radius:8px;">

          <!-- Header -->
          <tr>
            <td align="center" style="padding:30px 30px 20px; background-color:#4f46e5; border-radius:8px 8px 0 0;">
              <h1 style="margin:0; color:#ffffff; font-size:20px; font-weight:600; line-height:1.4;">
                Şəxsiyyət Testi Dəvətnaməsi
              </h1>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:28px 30px;">
              <p style="margin:0 0 16px; font-size:15px; line-height:1.6; color:#333333;">
                Salam,
              </p>
              <p style="margin:0 0 16px; font-size:15px; line-height:1.6; color:#333333;">
                <strong>{sender_name}</strong> Octopus platformasında sizinlə
                <strong>{credit_count}</strong> şəxsiyyət testi paylaşdı.
                Şəxsiyyət tipinizi kəşf edin və iş mühitiniz haqqında faydalı məlumatlar əldə edin.
              </p>

              <!-- CTA Button -->
              <table role="presentation" cellspacing="0" cellpadding="0" border="0" style="margin:24px auto;">
                <tr>
                  <td align="center" style="background-color:#4f46e5; border-radius:6px;">
                    <a href="{redeem_url}"
                       target="_blank"
                       style="display:inline-block; padding:12px 32px; color:#ffffff; text-decoration:none; font-size:15px; font-weight:600; font-family:Arial, Helvetica, sans-serif;">
                      Dəvətnaməyə Bax
                    </a>
                  </td>
                </tr>
              </table>

              <!-- Details -->
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color:#f9fafb; border:1px solid #e5e7eb; border-radius:6px; margin-top:20px;">
                <tr>
                  <td style="padding:14px 18px; border-bottom:1px solid #e5e7eb; font-size:13px; color:#6b7280; width:40%;">Göndərən</td>
                  <td style="padding:14px 18px; border-bottom:1px solid #e5e7eb; font-size:13px; color:#333333;">{sender_name}</td>
                </tr>
                <tr>
                  <td style="padding:14px 18px; border-bottom:1px solid #e5e7eb; font-size:13px; color:#6b7280;">Test sayı</td>
                  <td style="padding:14px 18px; border-bottom:1px solid #e5e7eb; font-size:13px; color:#333333;">{credit_count}</td>
                </tr>
                <tr>
                  <td style="padding:14px 18px; font-size:13px; color:#6b7280;">Etibarlıdır</td>
                  <td style="padding:14px 18px; font-size:13px; color:#333333;">{expires_str} tarixinə qədər</td>
                </tr>
              </table>

              <p style="margin:20px 0 0; font-size:12px; line-height:1.5; color:#9ca3af;">
                Linki brauzerə kopyalayın:
                <a href="{redeem_url}" style="color:#4f46e5; word-break:break-all; text-decoration:underline;">{redeem_url}</a>
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:20px 30px; border-top:1px solid #e5e7eb; background-color:#f9fafb; border-radius:0 0 8px 8px;">
              <p style="margin:0 0 6px; font-size:12px; color:#9ca3af; text-align:center;">
                Bu email {sender_name} adından Octopus tərəfindən göndərilib.
              </p>
              <p style="margin:0 0 6px; font-size:12px; color:#9ca3af; text-align:center;">
                Bu emaili gözləmirdinizsə, onu nəzərə almaya bilərsiniz.
              </p>
              <p style="margin:0; font-size:12px; color:#9ca3af; text-align:center;">
                Octopus - Şəxsiyyət Testi Platforması | <a href="https://octopus.com.az" style="color:#4f46e5; text-decoration:underline;">octopus.com.az</a>
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

        email_sent = True
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [invitation.recipient_email],
                html_message=html_message,
            )
        except Exception:
            email_sent = False

        return Response({
            'id': invitation.id,
            'token': str(invitation.token),
            'recipient_email': invitation.recipient_email,
            'credit_count': invitation.credit_count,
            'is_shareable': invitation.is_shareable,
            'expires_at': invitation.expires_at,
            'email_sent': email_sent,
            'redeem_url': redeem_url,
        }, status=status.HTTP_201_CREATED)


class MyInvitationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Lazy-expire pending invitations
        TestInvitation.objects.filter(
            sender=request.user,
            status='PENDING',
            expires_at__lt=timezone.now()
        ).update(status='EXPIRED')

        invitations = TestInvitation.objects.filter(sender=request.user)
        serializer = InvitationListSerializer(invitations, many=True)

        reserved = TestInvitation.objects.filter(
            sender=request.user, status='PENDING'
        ).aggregate(total=Sum('credit_count'))['total'] or 0

        return Response({
            'invitations': serializer.data,
            'total_credits': request.user.active_test_count,
            'reserved_credits': reserved,
            'available_credits': max(0, request.user.active_test_count - reserved),
        })


class RevokeInvitationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            invitation = TestInvitation.objects.get(
                pk=pk, sender=request.user, status='PENDING'
            )
        except TestInvitation.DoesNotExist:
            return Response(
                {'detail': 'Invitation not found or cannot be revoked.'},
                status=status.HTTP_404_NOT_FOUND
            )

        invitation.status = 'REVOKED'
        invitation.revoked_at = timezone.now()
        invitation.save()

        return Response({'detail': 'Invitation revoked successfully.'})


class ValidateTokenView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, token):
        try:
            invitation = TestInvitation.objects.get(token=token)
        except TestInvitation.DoesNotExist:
            return Response(
                {'detail': 'Invalid invitation link.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if invitation.is_expired:
            invitation.status = 'EXPIRED'
            invitation.save()

        serializer = InvitationDetailSerializer(invitation)
        return Response(serializer.data)


class RedeemInvitationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, token):
        with transaction.atomic():
            try:
                invitation = TestInvitation.objects.select_for_update().get(
                    token=token, status='PENDING'
                )
            except TestInvitation.DoesNotExist:
                return Response(
                    {'detail': 'Invitation not found, already used, or expired.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if invitation.is_expired:
                invitation.status = 'EXPIRED'
                invitation.save()
                return Response(
                    {'detail': 'This invitation has expired.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Enforce recipient email match when not shareable
            if not invitation.is_shareable:
                if request.user.email.lower() != invitation.recipient_email.lower():
                    return Response(
                        {'detail': 'This invitation can only be claimed by the original recipient.'},
                        status=status.HTTP_403_FORBIDDEN
                    )

            sender = CustomUser.objects.select_for_update().get(pk=invitation.sender_id)
            recipient = CustomUser.objects.select_for_update().get(pk=request.user.pk)

            # Verify sender still has enough credits for this invitation
            other_reserved = TestInvitation.objects.filter(
                sender=sender, status='PENDING'
            ).exclude(pk=invitation.pk).aggregate(
                total=Sum('credit_count')
            )['total'] or 0

            if sender.active_test_count - other_reserved < invitation.credit_count:
                return Response(
                    {'detail': 'Sender no longer has available credits for this invitation.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            sender.active_test_count = F('active_test_count') - invitation.credit_count
            sender.save(update_fields=['active_test_count'])

            recipient.active_test_count = F('active_test_count') + invitation.credit_count
            recipient.save(update_fields=['active_test_count'])

            invitation.status = 'REDEEMED'
            invitation.recipient = request.user
            invitation.redeemed_at = timezone.now()
            invitation.save()

        return Response({'detail': 'Test credit(s) claimed successfully!'})
