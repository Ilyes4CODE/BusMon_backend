from rest_framework import serializers, generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.accounts.models import User
from apps.accounts.serializers import UserSerializer
from apps.accounts.permissions import IsAdmin
from .models import DriverProfile, Absence
from .serializers import *

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
    permission_classes = [AllowAny]
 
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
 