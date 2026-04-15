"""
routes/serializers.py
"""

from rest_framework import serializers
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
        return instance


class TripSerializer(serializers.ModelSerializer):
    route_name   = serializers.CharField(source='route.name',             read_only=True)
    bus_plate    = serializers.CharField(source='bus.plate_number',       read_only=True)
    driver_name  = serializers.CharField(source='driver.get_full_name',   read_only=True)
    status_label = serializers.CharField(source='get_status_display',     read_only=True)
    route_stops  = StopSerializer(source='route.stops', many=True, read_only=True)

    class Meta:
        model  = Trip
        fields = [
            'id', 'route', 'route_name', 'route_stops', 'bus', 'bus_plate',
            'driver', 'driver_name', 'departure_time', 'arrival_time',
            'status', 'status_label', 'delay_minutes', 'notes', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']