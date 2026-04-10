"""
Bus Monitoring System - URL Configuration
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth
    path('api/auth/', include('apps.accounts.urls')),

    # Core APIs
    path('api/buses/', include('apps.buses.urls')),
    path('api/routes/', include('apps.routes.urls')),
    path('api/drivers/', include('apps.drivers.urls')),
    path('api/maintenance/', include('apps.maintenance.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    path('api/ratings/', include('apps.ratings.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# ── Flutter config endpoint ───────────────────────────────────────
from django.http import JsonResponse
from django.conf import settings
import socket

def flutter_config(request):
    """
    GET /api/config/
    Returns server IP and URLs so Flutter can discover the backend dynamically.
    Flutter calls this on first launch after IP scan finds the server.
    """
    host = request.get_host().split(':')[0]
    port = request.get_port()
    return JsonResponse({
        'api_url':   f'http://{host}:{port}/api/',
        'ws_url':    f'ws://{host}:{port}/ws/',
        'server_ip': host,
        'port':      int(port),
    })

urlpatterns += [
    path('api/config/', flutter_config, name='flutter-config'),
]