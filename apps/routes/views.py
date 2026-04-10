"""
routes/views.py
"""

from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.accounts.permissions import IsAdmin, IsAdminOrReadOnly, IsAdminOrDriver
from .models import Route, Trip
from .serializers import RouteSerializer, RouteWriteSerializer, TripSerializer


# ── Routes ───────────────────────────────────────────────────

class RouteListCreateView(generics.ListCreateAPIView):
    queryset           = Route.objects.prefetch_related('stops').filter(is_active=True)
    permission_classes = [IsAdminOrReadOnly]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RouteSerializer
        return RouteWriteSerializer


class RouteDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset           = Route.objects.prefetch_related('stops')
    permission_classes = [IsAdminOrReadOnly]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RouteSerializer
        return RouteWriteSerializer


# ── Trips ────────────────────────────────────────────────────

class TripListCreateView(generics.ListCreateAPIView):
    queryset           = Trip.objects.select_related('route', 'bus', 'driver')
    serializer_class   = TripSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        qs     = super().get_queryset()
        user   = self.request.user

        # Driver sees only his own trips
        if user.is_driver:
            return qs.filter(driver=user)

        # Filters
        driver_id = self.request.query_params.get('driver_id')
        bus_id    = self.request.query_params.get('bus_id')
        date      = self.request.query_params.get('date')   # format: YYYY-MM-DD
        status_f  = self.request.query_params.get('status')

        if driver_id: qs = qs.filter(driver_id=driver_id)
        if bus_id:    qs = qs.filter(bus_id=bus_id)
        if date:      qs = qs.filter(departure_time__date=date)
        if status_f:  qs = qs.filter(status=status_f)

        return qs


class TripDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset           = Trip.objects.select_related('route', 'bus', 'driver')
    serializer_class   = TripSerializer
    permission_classes = [IsAdminOrReadOnly]


class TripStatusUpdateView(APIView):
    """
    PATCH /api/routes/trips/{id}/status/
    Driver starts or ends a trip.
    """
    permission_classes = [IsAdminOrDriver]

    def patch(self, request, pk):
        try:
            trip = Trip.objects.get(pk=pk)
        except Trip.DoesNotExist:
            return Response({'error': 'Rotation introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get('status')
        if not new_status:
            return Response({'error': 'status requis.'}, status=status.HTTP_400_BAD_REQUEST)

        trip.status = new_status

        # Auto-update bus status based on trip status
        if new_status == Trip.Status.IN_PROGRESS and trip.bus:
            trip.bus.status = 'moving'
            trip.bus.save(update_fields=['status'])

        elif new_status in (Trip.Status.COMPLETED, Trip.Status.CANCELLED) and trip.bus:
            trip.bus.status = 'stopped'
            trip.bus.save(update_fields=['status'])

        if new_status == Trip.Status.COMPLETED:
            trip.arrival_time = timezone.now()

        trip.save()
        return Response(TripSerializer(trip).data)


class DriverScheduleView(APIView):
    """
    GET /api/routes/schedule/
    Returns today's trips for the authenticated driver,
    or for a specific driver if admin passes ?driver_id=X
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user      = request.user
        today     = timezone.now().date()
        driver_id = request.query_params.get('driver_id')

        if user.is_admin and driver_id:
            trips = Trip.objects.filter(driver_id=driver_id, departure_time__date=today)
        elif user.is_driver:
            trips = Trip.objects.filter(driver=user, departure_time__date=today)
        else:
            return Response({'error': 'Accès refusé.'}, status=status.HTTP_403_FORBIDDEN)

        return Response(TripSerializer(trips, many=True).data)