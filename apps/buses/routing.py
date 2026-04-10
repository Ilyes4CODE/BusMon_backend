"""
buses/routing.py
"""

from django.urls import path
from .consumers import BusLocationConsumer

websocket_urlpatterns = [
    path('ws/buses/', BusLocationConsumer.as_asgi()),
]