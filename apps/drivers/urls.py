"""
drivers/urls.py
"""

from django.urls import path
from .views import (
    DriverListView, DriverDetailView, CreateDriverView,
    AbsenceListCreateView, AbsenceDetailView,
)

urlpatterns = [
    path('',                     DriverListView.as_view(),       name='driver-list'),
    path('create/',              CreateDriverView.as_view(),     name='driver-create'),
    path('<int:pk>/',            DriverDetailView.as_view(),     name='driver-detail'),

    # Absences
    path('absences/',            AbsenceListCreateView.as_view(), name='absence-list'),
    path('absences/<int:pk>/',   AbsenceDetailView.as_view(),     name='absence-detail'),
]