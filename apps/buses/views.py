from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.accounts.permissions import IsAdmin, IsAdminOrReadOnly, IsAdminOrDriver
from .models import Bus
from .serializers import BusSerializer, BusLocationSerializer, BusStatusSerializer, BusListSerializer


class BusListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminOrReadOnly]

    def get_serializer_class(self):
        return BusSerializer

    def get_queryset(self):
        qs         = Bus.objects.filter(is_active=True).select_related('driver')
        status_val = self.request.query_params.get('status')
        if status_val:
            qs = qs.filter(status=status_val)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = BusSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            bus = serializer.save()
            # If a driver is assigned, update their availability
            if bus.driver:
                from apps.drivers.models import DriverProfile
                DriverProfile.objects.filter(user=bus.driver).update(is_available=False)
            return Response(BusSerializer(bus, context={'request': request}).data,
                            status=status.HTTP_201_CREATED)
        return Response({'errors': serializer.errors,
                         'detail': _flatten(serializer.errors)},
                        status=status.HTTP_400_BAD_REQUEST)


class BusDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset           = Bus.objects.select_related('driver')
    permission_classes = [IsAdminOrReadOnly]

    def get_serializer_class(self):
        return BusSerializer

    def update(self, request, *args, **kwargs):
        partial    = kwargs.pop('partial', False)
        instance   = self.get_object()
        old_driver = instance.driver

        serializer = BusSerializer(instance, data=request.data,
                                   partial=partial, context={'request': request})
        if serializer.is_valid():
            bus        = serializer.save()
            new_driver = bus.driver

            # Update driver availability
            from apps.drivers.models import DriverProfile
            if old_driver and old_driver != new_driver:
                DriverProfile.objects.filter(user=old_driver).update(is_available=True)
            if new_driver and new_driver != old_driver:
                DriverProfile.objects.filter(user=new_driver).update(is_available=False)

            return Response(BusSerializer(bus, context={'request': request}).data)
        return Response({'errors': serializer.errors,
                         'detail': _flatten(serializer.errors)},
                        status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        bus = self.get_object()
        if bus.driver:
            from apps.drivers.models import DriverProfile
            DriverProfile.objects.filter(user=bus.driver).update(is_available=True)
        bus.is_active = False
        bus.driver    = None
        bus.save()
        return Response({'message': 'Bus deactivated.'}, status=status.HTTP_200_OK)


class BusAssignDriverView(APIView):
    """
    PATCH /api/buses/{id}/assign-driver/
    Body: {"driver_id": 5}  or  {"driver_id": null}  to unassign
    """
    permission_classes = [IsAdmin]

    def patch(self, request, pk):
        try:
            bus = Bus.objects.select_related('driver').get(pk=pk)
        except Bus.DoesNotExist:
            return Response({'error': 'Bus not found.'}, status=status.HTTP_404_NOT_FOUND)

        from apps.accounts.models import User
        from apps.drivers.models import DriverProfile

        driver_id  = request.data.get('driver_id')
        old_driver = bus.driver

        if driver_id is None:
            # Unassign
            bus.driver = None
            bus.save(update_fields=['driver'])
            if old_driver:
                DriverProfile.objects.filter(user=old_driver).update(is_available=True)
            return Response({'message': 'Driver unassigned.', 'bus': BusSerializer(bus).data})

        try:
            new_driver = User.objects.get(pk=driver_id, role='driver')
        except User.DoesNotExist:
            return Response({'error': 'Driver not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Check uniqueness — one bus per driver
        existing = Bus.objects.filter(driver=new_driver, is_active=True).exclude(pk=pk).first()
        if existing:
            return Response({
                'error': f"{new_driver.get_full_name()} is already assigned to bus {existing.plate_number}."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Free old driver
        if old_driver and old_driver != new_driver:
            DriverProfile.objects.filter(user=old_driver).update(is_available=True)

        bus.driver = new_driver
        bus.save(update_fields=['driver'])
        DriverProfile.objects.filter(user=new_driver).update(is_available=False)

        return Response({'message': f"{new_driver.get_full_name()} assigned to {bus.plate_number}.",
                         'bus': BusSerializer(bus).data})


class MyBusView(APIView):
    """
    GET /api/buses/my-bus/
    Driver gets their assigned bus.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            bus = Bus.objects.get(driver=user, is_active=True)
            return Response(BusSerializer(bus, context={'request': request}).data)
        except Bus.DoesNotExist:
            return Response({'error': 'No bus assigned to you.', 'bus': None},
                            status=status.HTTP_404_NOT_FOUND)


class BusLocationUpdateView(APIView):
    permission_classes = [IsAdminOrDriver]

    def patch(self, request, pk):
        try:
            bus = Bus.objects.get(pk=pk)
        except Bus.DoesNotExist:
            return Response({'error': 'Bus not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Driver can only update their own assigned bus
        user = request.user
        if user.is_driver and bus.driver != user:
            return Response({'error': 'You can only update your assigned bus.'},
                            status=status.HTTP_403_FORBIDDEN)

        serializer = BusLocationSerializer(bus, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(last_location_update=timezone.now())
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BusStatusUpdateView(APIView):
    permission_classes = [IsAdminOrDriver]

    def patch(self, request, pk):
        try:
            bus = Bus.objects.get(pk=pk)
        except Bus.DoesNotExist:
            return Response({'error': 'Bus not found.'}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        if user.is_driver and bus.driver != user:
            return Response({'error': 'You can only update your assigned bus.'},
                            status=status.HTTP_403_FORBIDDEN)

        serializer = BusStatusSerializer(bus, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AllBusLocationsView(APIView):
    """GET /api/buses/locations/ — all active buses with GPS."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        buses = Bus.objects.filter(is_active=True).select_related('driver').exclude(latitude=None)
        return Response(BusListSerializer(buses, many=True).data)


def _flatten(errors: dict) -> str:
    parts = []
    for field, msgs in errors.items():
        label = field.replace('_', ' ').title()
        msg   = msgs[0] if isinstance(msgs, list) else str(msgs)
        parts.append(f'{label}: {msg}')
    return ' | '.join(parts)