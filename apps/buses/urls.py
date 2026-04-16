from django.urls import path
from .views import (
    BusListCreateView, BusDetailView,
    MyBusView,
    BusLocationUpdateView, BusStatusUpdateView,
    AllBusLocationsView,
)

urlpatterns = [
    path('',                         BusListCreateView.as_view(),    name='bus-list'),
    path('locations/',               AllBusLocationsView.as_view(),  name='bus-all-locations'),
    path('my-bus/',                  MyBusView.as_view(),            name='bus-my-bus'),
    path('<int:pk>/',                BusDetailView.as_view(),        name='bus-detail'),
    path('<int:pk>/location/',       BusLocationUpdateView.as_view(),name='bus-location'),
    path('<int:pk>/status/',         BusStatusUpdateView.as_view(),  name='bus-status'),
]