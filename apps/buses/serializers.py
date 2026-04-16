from rest_framework import serializers

from .models import Bus


class BusSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model  = Bus
        fields = [
            'id', 'plate_number', 'model', 'brand', 'capacity', 'year',
            'status', 'status_display',
            'latitude', 'longitude', 'last_location_update',
            'is_active', 'notes', 'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'last_location_update', 'status_display']


class BusLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Bus
        fields = ['id', 'plate_number', 'latitude', 'longitude',
                  'status', 'last_location_update']
        read_only_fields = ['id', 'plate_number', 'last_location_update']


class BusStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Bus
        fields = ['id', 'status']


class BusListSerializer(serializers.ModelSerializer):
    active_trip = serializers.SerializerMethodField()

    class Meta:
        model  = Bus
        fields = ['id', 'plate_number', 'brand', 'model', 'capacity', 'year',
                  'status',
                  'latitude', 'longitude', 'last_location_update', 'active_trip']

    def get_active_trip(self, obj):
        trips = getattr(obj, 'map_relevant_trips', None)
        trip = trips[0] if trips else None
        if not trip:
            return None
        return {
            'id': trip.id,
            'route_id': trip.route_id,
            'route_name': trip.route.name,
            'departure_time': trip.departure_time,
            'arrival_time': trip.arrival_time,
            'status': trip.status,
            'delay_minutes': trip.delay_minutes,
        }
