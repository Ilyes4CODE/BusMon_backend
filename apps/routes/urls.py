"""
routes/urls.py
"""

from django.urls import path
from .views import (
    RouteListCreateView, RouteDetailView,
    TripListCreateView, TripDetailView,
    TripStatusUpdateView, DriverScheduleView,
)

urlpatterns = [
    # Routes
    path('',                         RouteListCreateView.as_view(), name='route-list'),
    path('<int:pk>/',                RouteDetailView.as_view(),     name='route-detail'),

    # Trips
    path('trips/',                   TripListCreateView.as_view(),  name='trip-list'),
    path('trips/<int:pk>/',          TripDetailView.as_view(),      name='trip-detail'),
    path('trips/<int:pk>/status/',   TripStatusUpdateView.as_view(),name='trip-status'),

    # Driver schedule
    path('schedule/',                DriverScheduleView.as_view(),  name='driver-schedule'),
]