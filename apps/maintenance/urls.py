from django.urls import path
from .views import (
    MaintenanceListCreateView, MaintenanceDetailView,
    BreakdownListCreateView, BreakdownDetailView,
    SendBreakdownAlertView, ResolveBreakdownView,
)

urlpatterns = [
    path('',                                MaintenanceListCreateView.as_view(), name='maintenance-list'),
    path('<int:pk>/',                       MaintenanceDetailView.as_view(),     name='maintenance-detail'),
    path('breakdowns/',                     BreakdownListCreateView.as_view(),   name='breakdown-list'),
    path('breakdowns/<int:pk>/',            BreakdownDetailView.as_view(),       name='breakdown-detail'),
    path('breakdowns/<int:pk>/alert/',      SendBreakdownAlertView.as_view(),    name='breakdown-alert'),
    path('breakdowns/<int:pk>/resolve/',    ResolveBreakdownView.as_view(),      name='breakdown-resolve'),
]