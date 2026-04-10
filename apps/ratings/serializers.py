"""
apps/ratings/serializers.py
"""

from rest_framework import serializers
from .models import DriverRating
from apps.accounts.models import User


class DriverRatingSerializer(serializers.ModelSerializer):
    driver_name  = serializers.CharField(source='driver.get_full_name', read_only=True)
    rated_by_name= serializers.CharField(source='rated_by.get_full_name', read_only=True)

    class Meta:
        model  = DriverRating
        fields = ['id', 'driver', 'driver_name', 'rated_by', 'rated_by_name',
                  'trip', 'stars', 'comment', 'created_at']
        read_only_fields = ['id', 'rated_by', 'created_at']

    def validate(self, attrs):
        request = self.context['request']
        user    = request.user
        trip    = attrs.get('trip')

        # Check user hasn't already rated this trip
        if trip and DriverRating.objects.filter(rated_by=user, trip=trip).exists():
            raise serializers.ValidationError(
                'Vous avez déjà évalué ce chauffeur pour ce trajet.'
            )

        # Make sure driver field matches the trip's driver
        if trip and trip.driver and attrs.get('driver') != trip.driver:
            raise serializers.ValidationError(
                'Le chauffeur ne correspond pas à ce trajet.'
            )

        return attrs

    def create(self, validated_data):
        validated_data['rated_by'] = self.context['request'].user
        return super().create(validated_data)


class DriverAverageRatingSerializer(serializers.ModelSerializer):
    """Summary of a driver's ratings — used in driver profile."""
    average_stars = serializers.SerializerMethodField()
    total_ratings = serializers.SerializerMethodField()
    rating_breakdown = serializers.SerializerMethodField()

    class Meta:
        model  = User
        fields = ['id', 'first_name', 'last_name', 'average_stars',
                  'total_ratings', 'rating_breakdown']

    def get_average_stars(self, obj):
        from django.db.models import Avg
        result = obj.ratings_received.aggregate(avg=Avg('stars'))['avg']
        return round(result, 2) if result else 0.0

    def get_total_ratings(self, obj):
        return obj.ratings_received.count()

    def get_rating_breakdown(self, obj):
        """Returns count per star: {1: 2, 2: 0, 3: 5, 4: 10, 5: 8}"""
        breakdown = {i: 0 for i in range(1, 6)}
        for r in obj.ratings_received.values('stars'):
            breakdown[r['stars']] += 1
        return breakdown