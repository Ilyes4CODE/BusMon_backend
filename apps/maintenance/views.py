from rest_framework import serializers, generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from apps.accounts.permissions import IsAdmin, IsAdminOrDriver
from apps.buses.models import Bus
from .models import MaintenanceRecord, Breakdown
from .serializers import *

class MaintenanceListCreateView(generics.ListCreateAPIView):
    queryset           = MaintenanceRecord.objects.select_related('bus', 'created_by')
    serializer_class   = MaintenanceRecordSerializer
    permission_classes = [IsAdmin]
 
    def get_queryset(self):
        qs     = super().get_queryset()
        bus_id = self.request.query_params.get('bus_id')
        if bus_id:
            qs = qs.filter(bus_id=bus_id)
        return qs
 
 
class MaintenanceDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset           = MaintenanceRecord.objects.all()
    serializer_class   = MaintenanceRecordSerializer
    permission_classes = [IsAdmin]
 
 
class BreakdownListCreateView(generics.ListCreateAPIView):
    queryset           = Breakdown.objects.select_related('bus', 'reported_by')
    serializer_class   = BreakdownSerializer
    permission_classes = [IsAdminOrDriver]
 
    def get_queryset(self):
        qs   = super().get_queryset()
        user = self.request.user
        if user.is_driver:
            qs = qs.filter(reported_by=user)
        bus_id = self.request.query_params.get('bus_id')
        if bus_id:
            qs = qs.filter(bus_id=bus_id)
        return qs
 
 
class BreakdownDetailView(generics.RetrieveUpdateAPIView):
    queryset           = Breakdown.objects.all()
    serializer_class   = BreakdownSerializer
    permission_classes = [IsAdminOrDriver]
 
 
class SendBreakdownAlertView(APIView):
    """
    POST /api/maintenance/breakdowns/{id}/alert/
    Driver sends an alert when the bus breaks down.
    Broadcasts a notification to all admins automatically.
    """
    permission_classes = [IsAdminOrDriver]
 
    def post(self, request, pk):
        try:
            breakdown = Breakdown.objects.select_related('bus', 'reported_by').get(pk=pk)
        except Breakdown.DoesNotExist:
            return Response({'error': 'Panne introuvable.'}, status=status.HTTP_404_NOT_FOUND)
 
        if breakdown.alert_sent:
            return Response({'error': 'Alerte déjà envoyée pour cette panne.'},
                            status=status.HTTP_400_BAD_REQUEST)
 
        serializer = SendAlertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
 
        # Save alert
        breakdown.alert_sent    = True
        breakdown.alert_sent_at = timezone.now()
        breakdown.alert_message = serializer.validated_data['alert_message']
        breakdown.status        = Breakdown.BreakdownStatus.IN_PROGRESS
        breakdown.save(update_fields=['alert_sent', 'alert_sent_at',
                                      'alert_message', 'status'])
 
        # Create notification for all admins
        from apps.accounts.models import User
        from apps.notifications.models import Notification
 
        admins = User.objects.filter(role='admin')
        notifications = [
            Notification(
                recipient=admin,
                title=f"🚨 Alerte Panne — Bus {breakdown.bus.plate_number}",
                body=(
                    f"Chauffeur: {breakdown.reported_by.get_full_name()}\n"
                    f"Message: {breakdown.alert_message}\n"
                    f"Lieu: {breakdown.location_desc or 'Non précisé'}"
                ),
                type='breakdown',
                data={
                    'breakdown_id': breakdown.id,
                    'bus_id': breakdown.bus.id,
                    'bus_plate': breakdown.bus.plate_number,
                }
            )
            for admin in admins
        ]
        Notification.objects.bulk_create(notifications)
 
        return Response({
            'message': 'Alerte envoyée avec succès.',
            'alert_sent_at': breakdown.alert_sent_at,
            'notified_admins': admins.count(),
        })
 
 
class ResolveBreakdownView(APIView):
    """
    PATCH /api/maintenance/breakdowns/{id}/resolve/
    Admin or Driver resolves the breakdown.
    root_cause is REQUIRED — driver must explain what happened.
    Bus status automatically returns to 'stopped'.
    """
    permission_classes = [IsAdminOrDriver]
 
    def patch(self, request, pk):
        try:
            breakdown = Breakdown.objects.select_related('bus').get(pk=pk)
        except Breakdown.DoesNotExist:
            return Response({'error': 'Panne introuvable.'}, status=status.HTTP_404_NOT_FOUND)
 
        if breakdown.status == Breakdown.BreakdownStatus.RESOLVED:
            return Response({'error': 'Cette panne est déjà résolue.'},
                            status=status.HTTP_400_BAD_REQUEST)
 
        serializer = ResolveBreakdownSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
 
        breakdown.status          = Breakdown.BreakdownStatus.RESOLVED
        breakdown.root_cause      = serializer.validated_data['root_cause']
        breakdown.resolution_notes= serializer.validated_data.get('resolution_notes', '')
        breakdown.resolved_by     = request.user
        breakdown.resolved_at     = timezone.now()
        breakdown.save()
 
        # Bus returns to stopped status
        breakdown.bus.status = Bus.Status.STOPPED
        breakdown.bus.save(update_fields=['status'])
 
        # Notify admins that breakdown is resolved
        from apps.accounts.models import User
        from apps.notifications.models import Notification
 
        admins = User.objects.filter(role='admin')
        notifications = [
            Notification(
                recipient=admin,
                title=f"✅ Panne résolue — Bus {breakdown.bus.plate_number}",
                body=(
                    f"Cause: {breakdown.root_cause}\n"
                    f"Résolu par: {request.user.get_full_name()}"
                ),
                type='breakdown',
                data={
                    'breakdown_id': breakdown.id,
                    'bus_id': breakdown.bus.id,
                }
            )
            for admin in admins
        ]
        Notification.objects.bulk_create(notifications)
 
        return Response({
            'message': 'Panne résolue. Bus remis en service.',
            'root_cause': breakdown.root_cause,
            'resolved_at': breakdown.resolved_at,
            'bus_status': breakdown.bus.status,
        })