from django.urls import path
from .views import (
    SendInvitationView,
    MyInvitationsView,
    RevokeInvitationView,
    ValidateTokenView,
    RedeemInvitationView,
)

urlpatterns = [
    path('invitations/', MyInvitationsView.as_view(), name='my-invitations'),
    path('invitations/send/', SendInvitationView.as_view(), name='send-invitation'),
    path('invitations/<int:pk>/revoke/', RevokeInvitationView.as_view(), name='revoke-invitation'),
    path('redeem/validate/<uuid:token>/', ValidateTokenView.as_view(), name='validate-token'),
    path('redeem/<uuid:token>/', RedeemInvitationView.as_view(), name='redeem-invitation'),
]
