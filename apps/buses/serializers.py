from rest_framework import serializers
from apps.accounts.models import User
from .models import Bus


class BusSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    driver_name    = serializers.SerializerMethodField()
    driver_id      = serializers.PrimaryKeyRelatedField(
                         source='driver',
                         queryset=User.objects.filter(role='driver'),
                         allow_null=True,
                         required=False,
                     )

    class Meta:
        model  = Bus
        fields = [
            'id', 'plate_number', 'model', 'brand', 'capacity', 'year',
            'status', 'status_display',
            'driver_id', 'driver_name',
            'latitude', 'longitude', 'last_location_update',
            'is_active', 'notes', 'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'last_location_update',
                            'status_display', 'driver_name']

    def get_driver_name(self, obj):
        return obj.driver.get_full_name() if obj.driver else None

    def validate_driver_id(self, driver):
        """
        driver here is already a User instance resolved by PrimaryKeyRelatedField.
        Just check that this driver isn't already assigned to another bus.
        Note: the frontend must send user.id NOT driver_profile.id.
        """
        if driver is None:
            return driver
        instance = self.instance
        existing = Bus.objects.filter(driver=driver, is_active=True).first()
        if existing and existing != instance:
            raise serializers.ValidationError(
                f"{driver.get_full_name()} is already assigned to bus {existing.plate_number}. "
                f"Unassign them first."
            )
        return driver


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
    driver_name = serializers.SerializerMethodField()

    class Meta:
        model  = Bus
        fields = ['id', 'plate_number', 'brand', 'model', 'capacity', 'year',
                  'status', 'driver_id', 'driver_name',
                  'latitude', 'longitude', 'last_location_update']

    def get_driver_name(self, obj):
        return obj.driver.get_full_name() if obj.driver else None