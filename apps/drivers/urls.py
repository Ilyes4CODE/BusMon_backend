"""
drivers/urls.py
"""

from django.urls import path
from .views import (
    DriverListView, DriverDetailView, CreateDriverView,
    AbsenceListCreateView, AbsenceDetailView,
    AbsenceHistoryListView, AbsenceHistoryDetailView,
    MarkDriverAbsentTodayView,
)

urlpatterns = [
    path('',                     DriverListView.as_view(),       name='driver-list'),
    path('create/',              CreateDriverView.as_view(),     name='driver-create'),
    path('<int:pk>/',            DriverDetailView.as_view(),     name='driver-detail'),

    # Absences
    path('absences/',            AbsenceListCreateView.as_view(), name='absence-list'),
    path('absences/<int:pk>/',   AbsenceDetailView.as_view(),     name='absence-detail'),

    path('absence-history/',           AbsenceHistoryListView.as_view(),   name='absence-history-list'),
    path('absence-history/<int:pk>/', AbsenceHistoryDetailView.as_view(), name='absence-history-detail'),
    path('<int:driver_id>/mark-absent-today/', MarkDriverAbsentTodayView.as_view(), name='driver-mark-absent-today'),
]