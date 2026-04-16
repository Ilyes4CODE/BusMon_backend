from django.db.models import Q
from django.utils import timezone
from django.db.models import Prefetch
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.accounts.permissions import IsAdmin, IsAdminOrReadOnly, IsAdminOrDriver
from apps.routes.models import Trip
from .models import Bus
from .serializers import BusSerializer, BusLocationSerializer, BusStatusSerializer, BusListSerializer


class BusListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminOrReadOnly]

    def get_serializer_class(self):
        return BusSerializer

    def get_queryset(self):
        qs         = Bus.objects.filter(is_active=True)
        status_val = self.request.query_params.get('status')
        if status_val:
            qs = qs.filter(status=status_val)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = BusSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            bus = serializer.save()
            return Response(BusSerializer(bus, context={'request': request}).data,
                            status=status.HTTP_201_CREATED)
        return Response({'errors': serializer.errors,
                         'detail': _flatten(serializer.errors)},
                        status=status.HTTP_400_BAD_REQUEST)


class BusDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset           = Bus.objects.all()
    permission_classes = [IsAdminOrReadOnly]

    def get_serializer_class(self):
        return BusSerializer

    def update(self, request, *args, **kwargs):
        partial    = kwargs.pop('partial', False)
        instance   = self.get_object()
        serializer = BusSerializer(instance, data=request.data,
                                   partial=partial, context={'request': request})
        if serializer.is_valid():
            bus = serializer.save()
            return Response(BusSerializer(bus, context={'request': request}).data)
        return Response({'errors': serializer.errors,
                         'detail': _flatten(serializer.errors)},
                        status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        bus = self.get_object()
        bus.is_active = False
        bus.save()
        return Response({'message': 'Bus deactivated.'}, status=status.HTTP_200_OK)


class MyBusView(APIView):
    """
    GET /api/buses/my-bus/
    Bus for the current trip (primary or second driver) — not a permanent bus assignment.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if not user.is_driver:
            return Response({'error': 'Drivers only.'}, status=status.HTTP_403_FORBIDDEN)

        trips = (
            Trip.objects.filter(
                Q(driver=user) | Q(second_driver=user),
                bus__isnull=False,
                status__in=[
                    Trip.Status.SCHEDULED,
                    Trip.Status.IN_PROGRESS,
                    Trip.Status.DELAYED,
                ],
            )
            .select_related('bus')
            .order_by('departure_time')
        )
        trip = trips.first()
        if not trip or not trip.bus:
            return Response({'error': 'Aucun bus pour un trajet en cours ou à venir.', 'bus': None},
                            status=status.HTTP_404_NOT_FOUND)
        return Response(BusSerializer(trip.bus, context={'request': request}).data)


def _driver_may_update_bus(user, bus: Bus) -> bool:
    if not user.is_driver:
        return True
    return Trip.objects.filter(
        bus=bus,
        status__in=[
            Trip.Status.SCHEDULED,
            Trip.Status.IN_PROGRESS,
            Trip.Status.DELAYED,
        ],
    ).filter(Q(driver=user) | Q(second_driver=user)).exists()


class BusLocationUpdateView(APIView):
    permission_classes = [IsAdminOrDriver]

    def patch(self, request, pk):
        try:
            bus = Bus.objects.get(pk=pk)
        except Bus.DoesNotExist:
            return Response({'error': 'Bus not found.'}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        if user.is_driver and not _driver_may_update_bus(user, bus):
            return Response({'error': 'Vous ne pouvez mettre à jour la position que pour le bus de votre trajet en cours.'},
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
        if user.is_driver and not _driver_may_update_bus(user, bus):
            return Response({'error': 'Vous ne pouvez mettre à jour que le bus de votre trajet en cours.'},
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
        trips_prefetch = Prefetch(
            'trips',
            queryset=Trip.objects.select_related('route').filter(
                status__in=[Trip.Status.SCHEDULED, Trip.Status.IN_PROGRESS, Trip.Status.DELAYED]
            ).order_by('departure_time'),
            to_attr='map_relevant_trips',
        )
        buses = Bus.objects.filter(is_active=True).prefetch_related(
            trips_prefetch
        ).exclude(latitude=None)
        return Response(BusListSerializer(buses, many=True).data)


def _flatten(errors: dict) -> str:
    parts = []
    for field, msgs in errors.items():
        label = field.replace('_', ' ').title()
        msg   = msgs[0] if isinstance(msgs, list) else str(msgs)
        parts.append(f'{label}: {msg}')
    return ' | '.join(parts)
