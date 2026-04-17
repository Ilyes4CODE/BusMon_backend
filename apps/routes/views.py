"""
routes/views.py
"""

from django.db.models import Q
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
    queryset           = Trip.objects.select_related(
        'route', 'bus', 'driver', 'second_driver',
    ).prefetch_related('route__stops')
    serializer_class   = TripSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method in ('POST',):
            return [IsAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs     = super().get_queryset()
        user   = self.request.user

        # Driver sees trips where they are primary or second driver
        if user.is_driver:
            qs = qs.filter(Q(driver=user) | Q(second_driver=user))

        # Filters
        driver_id = self.request.query_params.get('driver_id')
        bus_id    = self.request.query_params.get('bus_id')
        date      = self.request.query_params.get('date')   # format: YYYY-MM-DD
        status_f  = self.request.query_params.get('status')
        start_at  = self.request.query_params.get('start_at')  # ISO datetime
        end_at    = self.request.query_params.get('end_at')    # ISO datetime

        if driver_id: qs = qs.filter(driver_id=driver_id)
        if bus_id:    qs = qs.filter(bus_id=bus_id)
        if date:      qs = qs.filter(departure_time__date=date)
        if status_f:  qs = qs.filter(status=status_f)
        if start_at:  qs = qs.filter(departure_time__gte=start_at)
        if end_at:    qs = qs.filter(departure_time__lte=end_at)

        return qs


class TripDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset           = Trip.objects.select_related(
        'route', 'bus', 'driver', 'second_driver',
    ).prefetch_related('route__stops')
    serializer_class   = TripSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH', 'DELETE'):
            return [IsAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_driver:
            return qs.filter(Q(driver=user) | Q(second_driver=user))
        return qs


class AdminTripManageView(APIView):
    """
    PATCH /api/routes/admin/trips/{id}/
    DELETE /api/routes/admin/trips/{id}/
    Admin-only endpoint to modify or delete a trip.
    """
    permission_classes = [IsAdmin]

    def patch(self, request, pk):
        try:
            trip = Trip.objects.select_related(
                'route', 'bus', 'driver', 'second_driver',
            ).prefetch_related('route__stops').get(pk=pk)
        except Trip.DoesNotExist:
            return Response({'error': 'Rotation introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = TripSerializer(trip, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        try:
            trip = Trip.objects.get(pk=pk)
        except Trip.DoesNotExist:
            return Response({'error': 'Rotation introuvable.'}, status=status.HTTP_404_NOT_FOUND)
        trip.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TripStatusUpdateView(APIView):
    """
    PATCH /api/routes/trips/{id}/status/
    Driver starts or ends a trip.
    """
    permission_classes = [IsAdminOrDriver]

    def patch(self, request, pk):
        try:
            trip = Trip.objects.select_related('driver', 'second_driver', 'bus').get(pk=pk)
        except Trip.DoesNotExist:
            return Response({'error': 'Rotation introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        if user.is_driver and trip.driver_id != user.id and trip.second_driver_id != user.id:
            return Response({'error': 'Vous ne pouvez modifier que vos propres trajets.'}, status=status.HTTP_403_FORBIDDEN)

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
            trips = Trip.objects.filter(driver_id=driver_id, departure_time__date=today).select_related(
                'route', 'bus', 'driver', 'second_driver'
            ).prefetch_related('route__stops')
        elif user.is_driver:
            trips = Trip.objects.filter(
                Q(driver=user) | Q(second_driver=user),
                departure_time__date=today,
            ).select_related(
                'route', 'bus', 'driver', 'second_driver'
            ).prefetch_related('route__stops')
        else:
            return Response({'error': 'Accès refusé.'}, status=status.HTTP_403_FORBIDDEN)

        return Response(TripSerializer(trips, many=True).data)


class MyTripsView(APIView):
    """
    GET /api/routes/my-trips/
    Drivers get only their trips with optional filtering:
      - ?scope=today|upcoming|all (default=today)
      - ?date=YYYY-MM-DD
    Admins can inspect a driver timeline via:
      - ?driver_id=X
      - ?start_at=ISO_DATETIME
      - ?end_at=ISO_DATETIME
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        qs = Trip.objects.select_related('route', 'bus', 'driver', 'second_driver').prefetch_related('route__stops')
        scope = request.query_params.get('scope', 'today')
        date = request.query_params.get('date')
        start_at = request.query_params.get('start_at')
        end_at = request.query_params.get('end_at')
        driver_id = request.query_params.get('driver_id')
        now = timezone.now()

        if user.is_driver:
            qs = qs.filter(Q(driver=user) | Q(second_driver=user))
        elif user.is_admin:
            if driver_id:
                qs = qs.filter(driver_id=driver_id)
        else:
            return Response({'error': 'Accès refusé.'}, status=status.HTTP_403_FORBIDDEN)

        if date:
            qs = qs.filter(departure_time__date=date)
        elif scope == 'today':
            qs = qs.filter(departure_time__date=now.date())
        elif scope == 'upcoming':
            qs = qs.filter(departure_time__gte=now)

        if start_at:
            qs = qs.filter(departure_time__gte=start_at)
        if end_at:
            qs = qs.filter(departure_time__lte=end_at)

        return Response(TripSerializer(qs, many=True).data)