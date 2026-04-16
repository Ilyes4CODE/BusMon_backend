"""
routes/serializers.py
"""

from rest_framework import serializers

from apps.routes.constants import LONG_TRIP_KM
from apps.routes.geo import route_distance_km

from .models import Route, Stop, Trip


class StopSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Stop
        fields = ['id', 'name', 'order', 'lat', 'lng']


class RouteSerializer(serializers.ModelSerializer):
    stops = StopSerializer(many=True, read_only=True)

    class Meta:
        model  = Route
        fields = ['id', 'name', 'origin', 'destination',
                  'distance_km', 'duration_min', 'is_active',
                  'stops', 'created_at']
        read_only_fields = ['id', 'created_at']


class RouteWriteSerializer(serializers.ModelSerializer):
    stops = StopSerializer(many=True, required=False)

    class Meta:
        model  = Route
        # Include id so create/update responses return the route primary key (needed by clients linking trips).
        fields = ['id', 'name', 'origin', 'destination',
                  'distance_km', 'duration_min', 'is_active', 'stops']
        read_only_fields = ['id']

    def create(self, validated_data):
        stops_data = validated_data.pop('stops', [])
        route = Route.objects.create(**validated_data)
        for stop_data in stops_data:
            Stop.objects.create(route=route, **stop_data)
        if route.distance_km is None:
            d = route_distance_km(route)
            if d is not None:
                route.distance_km = d
                route.save(update_fields=['distance_km'])
        return route

    def update(self, instance, validated_data):
        stops_data = validated_data.pop('stops', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if stops_data is not None:
            instance.stops.all().delete()
            for stop_data in stops_data:
                Stop.objects.create(route=instance, **stop_data)
        if instance.distance_km is None or stops_data is not None:
            d = route_distance_km(instance)
            if d is not None:
                instance.distance_km = d
                instance.save(update_fields=['distance_km'])
        return instance


class TripSerializer(serializers.ModelSerializer):
    route_name   = serializers.CharField(source='route.name',             read_only=True)
    bus_plate    = serializers.CharField(source='bus.plate_number',       read_only=True)
    driver_name  = serializers.CharField(source='driver.get_full_name',   read_only=True)
    second_driver_name = serializers.CharField(
        source='second_driver.get_full_name', read_only=True, allow_null=True
    )
    status_label = serializers.CharField(source='get_status_display',     read_only=True)
    route_stops  = StopSerializer(source='route.stops', many=True, read_only=True)

    class Meta:
        model  = Trip
        fields = [
            'id', 'route', 'route_name', 'route_stops', 'bus', 'bus_plate',
            'driver', 'driver_name', 'second_driver', 'second_driver_name',
            'departure_time', 'arrival_time',
            'status', 'status_label', 'delay_minutes', 'notes', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def validate(self, attrs):
        route = attrs.get('route') or (self.instance.route if self.instance else None)
        driver = attrs.get('driver')
        if driver is None and self.instance is not None:
            driver = self.instance.driver
        second = attrs.get('second_driver')
        if second is None and self.instance is not None:
            second = self.instance.second_driver
        if route is None:
            return attrs
        dist = route_distance_km(route)
        if dist is not None and dist > LONG_TRIP_KM:
            if not second:
                raise serializers.ValidationError({
                    'second_driver': f'Un second conducteur est obligatoire pour les trajets de plus de {LONG_TRIP_KM} km.',
                })
            if driver and second and driver.pk == second.pk:
                raise serializers.ValidationError({
                    'second_driver': 'Le second conducteur doit être différent du conducteur principal.',
                })
        elif dist is not None and second:
            raise serializers.ValidationError({
                'second_driver': f'Le second conducteur n\'est requis que si la distance dépasse {LONG_TRIP_KM} km.',
            })
        return attrs