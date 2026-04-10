"""
apps/ratings/views.py
"""

from django.db.models import Avg
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.accounts.models import User
from apps.accounts.permissions import IsAdmin
from .models import DriverRating
from .serializers import DriverRatingSerializer, DriverAverageRatingSerializer


class SubmitRatingView(generics.CreateAPIView):
    """
    POST /api/ratings/
    Any authenticated user (role=user) can rate a driver.
    """
    serializer_class   = DriverRatingSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        from rest_framework.permissions import IsAuthenticated
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(rated_by=self.request.user)

    def create(self, request, *args, **kwargs):
        # Only users with role=user can rate
        if request.user.role not in ('user', 'admin'):
            return Response(
                {'error': 'Seuls les utilisateurs peuvent noter les chauffeurs.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)


class DriverRatingsListView(generics.ListAPIView):
    """
    GET /api/ratings/driver/{driver_id}/
    Get all ratings for a specific driver.
    """
    serializer_class   = DriverRatingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        driver_id = self.kwargs['driver_id']
        return DriverRating.objects.filter(
            driver_id=driver_id
        ).select_related('rated_by', 'trip')


class DriverAverageRatingView(APIView):
    """
    GET /api/ratings/driver/{driver_id}/average/
    Returns average stars + breakdown for a driver.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, driver_id):
        try:
            driver = User.objects.get(pk=driver_id, role='driver')
        except User.DoesNotExist:
            return Response({'error': 'Chauffeur introuvable.'},
                            status=status.HTTP_404_NOT_FOUND)

        serializer = DriverAverageRatingSerializer(driver)
        return Response(serializer.data)


class AllDriversRankingView(APIView):
    """
    GET /api/ratings/ranking/
    Returns all drivers ranked by average rating. Admin only.
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        drivers = User.objects.filter(role='driver').annotate(
            avg_stars=Avg('ratings_received__stars')
        ).order_by('-avg_stars')

        result = []
        for d in drivers:
            result.append({
                'driver_id':   d.id,
                'name':        d.get_full_name(),
                'avg_stars':   round(d.avg_stars, 2) if d.avg_stars else 0.0,
                'total_ratings': d.ratings_received.count(),
            })
        return Response(result)


class MyRatingsView(generics.ListAPIView):
    """
    GET /api/ratings/mine/
    Returns ratings submitted by the current user.
    """
    serializer_class   = DriverRatingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DriverRating.objects.filter(
            rated_by=self.request.user
        ).select_related('driver', 'trip')