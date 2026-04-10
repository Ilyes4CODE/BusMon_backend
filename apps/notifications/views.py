from django.db import models as db_models
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.accounts.models import User
from apps.accounts.permissions import IsAdmin
from .models import Notification
from .serializers import NotificationSerializer


def _user_notifications(user):
    """Base queryset — notifications addressed to this user OR broadcast (recipient=null)."""
    return Notification.objects.filter(
        db_models.Q(recipient=user) | db_models.Q(recipient__isnull=True)
    ).order_by('-created_at')


class NotificationListView(generics.ListAPIView):
    """
    GET /api/notifications/
    Returns personal + broadcast notifications for the authenticated user.
    """
    serializer_class   = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return _user_notifications(self.request.user)


class UnreadCountView(APIView):
    """GET /api/notifications/unread-count/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = _user_notifications(request.user).filter(is_read=False).count()
        return Response({'unread_count': count})


class MarkReadView(APIView):
    """
    PATCH /api/notifications/{id}/read/
    Works for both personal AND broadcast notifications.
    For broadcasts: creates a per-user read-receipt so we don't mutate shared state.
    Simple approach: if notification belongs to this user OR is broadcast, mark is_read=True.
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            notif = Notification.objects.get(pk=pk)
        except Notification.DoesNotExist:
            return Response({'error': 'Notification not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Allow if addressed to this user OR broadcast
        if notif.recipient is not None and notif.recipient != request.user:
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        notif.is_read = True
        notif.save(update_fields=['is_read'])
        return Response({'message': 'Marked as read.', 'id': pk})


class MarkAllReadView(APIView):
    """PATCH /api/notifications/mark-all-read/"""
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        updated = _user_notifications(request.user).filter(is_read=False).update(is_read=True)
        return Response({'message': f'{updated} notifications marked as read.', 'count': updated})


class DeleteNotificationView(APIView):
    """DELETE /api/notifications/{id}/"""
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            notif = Notification.objects.get(pk=pk)
        except Notification.DoesNotExist:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        if notif.recipient is not None and notif.recipient != request.user:
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        # Only admin can delete broadcast notifications
        if notif.recipient is None and not request.user.is_admin:
            return Response({'error': 'Only admins can delete broadcast notifications.'},
                            status=status.HTTP_403_FORBIDDEN)

        notif.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SendNotificationView(APIView):
    """
    POST /api/notifications/send/
    Admin sends a notification to one user or broadcasts to all (recipient_id=null).
    Body: { title, body, type, recipient_id (optional), target_role (optional) }
    """
    permission_classes = [IsAdmin]

    def post(self, request):
        title        = request.data.get('title', '').strip()
        body         = request.data.get('body', '').strip()
        notif_type   = request.data.get('type', 'general')
        recipient_id = request.data.get('recipient_id')
        target_role  = request.data.get('target_role')    # 'driver' | 'user' | 'all'
        data_payload = request.data.get('data')

        if not title or not body:
            return Response({'error': 'title and body are required.'},
                            status=status.HTTP_400_BAD_REQUEST)

        created = []

        if recipient_id:
            # Single recipient
            try:
                recipient = User.objects.get(pk=recipient_id)
            except User.DoesNotExist:
                return Response({'error': 'Recipient not found.'}, status=status.HTTP_404_NOT_FOUND)

            notif = Notification.objects.create(
                title=title, body=body, type=notif_type,
                recipient=recipient, data=data_payload,
            )
            created.append(notif)

        elif target_role and target_role != 'all':
            # Send to all users of a specific role
            users = User.objects.filter(role=target_role, is_active=True)
            notifications = [
                Notification(title=title, body=body, type=notif_type,
                             recipient=u, data=data_payload)
                for u in users
            ]
            created = Notification.objects.bulk_create(notifications)

        else:
            # Broadcast — null recipient = everyone sees it
            notif = Notification.objects.create(
                title=title, body=body, type=notif_type,
                recipient=None, data=data_payload,
            )
            created.append(notif)

        return Response({
            'message': f'{len(created)} notification(s) sent.',
            'notifications': NotificationSerializer(created, many=True).data,
        }, status=status.HTTP_201_CREATED)


class NotificationStatsView(APIView):
    """GET /api/notifications/stats/ — Admin dashboard stats."""
    permission_classes = [IsAdmin]

    def get(self, request):
        total    = Notification.objects.count()
        unread   = Notification.objects.filter(is_read=False).count()
        by_type  = {}
        for t in Notification.NotifType:
            by_type[t.value] = Notification.objects.filter(type=t.value).count()
        return Response({'total': total, 'unread': unread, 'by_type': by_type})