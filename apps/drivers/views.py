from rest_framework import serializers, generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from apps.accounts.models import User
from apps.accounts.serializers import UserSerializer
from apps.accounts.permissions import IsAdmin
from .models import Absence, AbsenceHistory, DriverProfile
from .serializers import (
    AbsenceHistorySerializer,
    AbsenceSerializer,
    DriverProfileSerializer,
    DriverProfileWriteSerializer,
)

class DriverListView(generics.ListAPIView):
    """GET /api/drivers/ — list all drivers with their profiles."""
    serializer_class   = DriverProfileSerializer
    permission_classes = [IsAdmin]
 
    def get_queryset(self):
        qs           = DriverProfile.objects.select_related('user')
        is_available = self.request.query_params.get('available')
        if is_available == 'true':
            qs = qs.filter(is_available=True)
        return qs
 
 
class DriverDetailView(generics.RetrieveUpdateAPIView):
    """GET/PUT /api/drivers/{id}/ — driver profile detail."""
    queryset           = DriverProfile.objects.select_related('user')
    permission_classes = [IsAdmin]
 
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return DriverProfileSerializer
        return DriverProfileWriteSerializer
 
 
class CreateDriverView(APIView):
    """
    POST /api/drivers/create/
    Creates a User with role=driver AND their DriverProfile in one call.
    """
    permission_classes = [IsAdmin]
 
    def post(self, request):
        from apps.accounts.serializers import RegisterSerializer
 
        # 1. Create user
        user_data = request.data.copy()
        user_data['role'] = 'driver'
        user_serializer = RegisterSerializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()
 
        # 2. Create driver profile
        profile_data = {
            'license_number':   request.data.get('license_number', ''),
            'license_expiry':   request.data.get('license_expiry', '2025-01-01'),
            'experience_years': request.data.get('experience_years', 0),
        }
        profile_serializer = DriverProfileWriteSerializer(data=profile_data)
        if profile_serializer.is_valid():
            profile_serializer.save(user=user)
 
        return Response({
            'message': 'Chauffeur créé avec succès.',
            'user':    UserSerializer(user).data,
        }, status=status.HTTP_201_CREATED)
 
 
# ── Absences ─────────────────────────────────────────────────
 
class AbsenceListCreateView(generics.ListCreateAPIView):
    queryset           = Absence.objects.select_related('driver')
    serializer_class   = AbsenceSerializer
    permission_classes = [IsAdmin]
 
    def get_queryset(self):
        qs        = super().get_queryset()
        driver_id = self.request.query_params.get('driver_id')
        month     = self.request.query_params.get('month')  # YYYY-MM
        if driver_id:
            qs = qs.filter(driver_id=driver_id)
        if month:
            year, m = month.split('-')
            qs = qs.filter(start_date__year=year, start_date__month=m)
        return qs
 
 
class AbsenceDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset           = Absence.objects.all()
    serializer_class   = AbsenceSerializer
    permission_classes = [IsAdmin]


class AbsenceHistoryListView(generics.ListAPIView):
    """GET /api/drivers/absence-history/ — daily absence log (all drivers)."""

    serializer_class   = AbsenceHistorySerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        qs = AbsenceHistory.objects.select_related('driver').order_by('-date', 'driver__last_name')
        driver_id = self.request.query_params.get('driver_id')
        month = self.request.query_params.get('month')  # YYYY-MM
        if driver_id:
            qs = qs.filter(driver_id=driver_id)
        if month:
            year, m = month.split('-')
            qs = qs.filter(date__year=year, date__month=m)
        return qs


class AbsenceHistoryDetailView(generics.RetrieveUpdateAPIView):
    queryset           = AbsenceHistory.objects.select_related('driver')
    serializer_class   = AbsenceHistorySerializer
    permission_classes = [IsAdmin]


class MarkDriverAbsentTodayView(APIView):
    """
    POST /api/drivers/<driver_id>/mark-absent-today/
    Marks the driver's daily absence-history row as ABSENT for today.
    """
    permission_classes = [IsAdmin]

    def post(self, request, driver_id):
        user = User.objects.filter(
            id=driver_id,
            role=User.Role.DRIVER,
            driver_profile__isnull=False,
        ).first()
        if not user:
            return Response({'error': 'Driver not found.'}, status=status.HTTP_404_NOT_FOUND)

        today = timezone.localdate()
        notes = (request.data.get('notes') or '').strip()

        row, created = AbsenceHistory.objects.get_or_create(
            driver=user,
            date=today,
            defaults={
                'status': AbsenceHistory.DayStatus.ABSENT,
                'notes': notes,
                'auto_generated': False,
            },
        )
        if not created:
            row.status = AbsenceHistory.DayStatus.ABSENT
            if notes:
                row.notes = notes
            row.auto_generated = False
            row.save(update_fields=['status', 'notes', 'auto_generated', 'updated_at'])

        return Response(AbsenceHistorySerializer(row).data, status=status.HTTP_200_OK)
