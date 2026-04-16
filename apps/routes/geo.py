"""Geodesic helpers for route distance."""

from __future__ import annotations

from math import asin, cos, radians, sin, sqrt

from .models import Route


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in km between two WGS84 points."""
    r_km = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    )
    c = 2 * asin(sqrt(min(1.0, a)))
    return r_km * c


def route_distance_km(route: Route) -> float | None:
    """Return route length in km: stored value, or computed from first/last stop coordinates."""
    if route.distance_km is not None:
        return float(route.distance_km)
    stops = list(route.stops.order_by("order"))
    if len(stops) < 2:
        return None
    a, b = stops[0], stops[-1]
    if a.lat is None or a.lng is None or b.lat is None or b.lng is None:
        return None
    return haversine_km(float(a.lat), float(a.lng), float(b.lat), float(b.lng))
