from rest_framework import serializers, generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from apps.accounts.models import User
from apps.accounts.serializers import UserSerializer, RegisterSerializer
from apps.accounts.permissions import IsAdmin
from .models import DriverProfile, Absence


class DriverProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model  = DriverProfile
        fields = ['id', 'user', 'license_number', 'license_expiry',
                  'experience_years', 'is_available', 'created_at']
        read_only_fields = ['id', 'created_at']


class DriverProfileWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model  = DriverProfile
        fields = ['license_number', 'license_expiry', 'experience_years', 'is_available']


class AbsenceSerializer(serializers.ModelSerializer):
    driver_name = serializers.CharField(source='driver.get_full_name', read_only=True)
    type_label  = serializers.CharField(source='get_type_display', read_only=True)
    class Meta:
        model  = Absence
        fields = ['id', 'driver', 'driver_name', 'start_date', 'end_date',
                  'type', 'type_label', 'reason', 'created_at']
        read_only_fields = ['id', 'created_at']


class DriverListView(generics.ListAPIView):
    serializer_class   = DriverProfileSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        qs = DriverProfile.objects.select_related('user')
        if self.request.query_params.get('available') == 'true':
            qs = qs.filter(is_available=True)
        return qs


class DriverDetailView(generics.RetrieveUpdateAPIView):
    queryset           = DriverProfile.objects.select_related('user')
    permission_classes = [IsAdmin]

    def get_serializer_class(self):
        return DriverProfileSerializer if self.request.method == 'GET' else DriverProfileWriteSerializer


class CreateDriverView(APIView):
    """
    POST /api/drivers/create/
    Public — allows self-registration as driver OR admin creating a driver.
    Returns full validation errors so Flutter can display them.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data.copy()

        # Force role to driver
        data['role'] = 'driver'

        # Remove username — will be auto-generated in serializer
        data.pop('username', None)

        # Validate and create user
        user_serializer = RegisterSerializer(data=data)
        if not user_serializer.is_valid():
            # Return human-readable errors
            errors = {}
            for field, msgs in user_serializer.errors.items():
                errors[field] = msgs[0] if isinstance(msgs, list) else str(msgs)
            return Response({'errors': errors, 'detail': _flatten_errors(errors)},
                            status=status.HTTP_400_BAD_REQUEST)

        user = user_serializer.save()

        # Create driver profile
        license_number   = request.data.get('license_number', '')
        license_expiry   = request.data.get('license_expiry', '2026-01-01')
        experience_years = request.data.get('experience_years', 0)

        profile_data = {
            'license_number':   license_number,
            'license_expiry':   license_expiry,
            'experience_years': experience_years,
        }
        profile_serializer = DriverProfileWriteSerializer(data=profile_data)
        if profile_serializer.is_valid():
            profile_serializer.save(user=user)
        else:
            # User created but profile failed — still return success, profile errors as warning
            return Response({
                'message':       'Driver account created. Profile setup incomplete.',
                'user':          UserSerializer(user).data,
                'profile_errors': profile_serializer.errors,
            }, status=status.HTTP_201_CREATED)

        return Response({
            'message': 'Driver account created successfully.',
            'user':    UserSerializer(user).data,
        }, status=status.HTTP_201_CREATED)


def _flatten_errors(errors: dict) -> str:
    """Turn {field: msg} dict into a single readable string."""
    parts = []
    for field, msg in errors.items():
        if field == 'non_field_errors':
            parts.append(str(msg))
        else:
            parts.append(f'{field.replace("_", " ").title()}: {msg}')
    return ' | '.join(parts)


class AbsenceListCreateView(generics.ListCreateAPIView):
    queryset           = Absence.objects.select_related('driver')
    serializer_class   = AbsenceSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        qs        = super().get_queryset()
        driver_id = self.request.query_params.get('driver_id')
        month     = self.request.query_params.get('month')
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