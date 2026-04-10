"""
apps/ratings/urls.py
"""

from django.urls import path
from .views import (
    SubmitRatingView,
    DriverRatingsListView,
    DriverAverageRatingView,
    AllDriversRankingView,
    MyRatingsView,
)

urlpatterns = [
    path('',                                  SubmitRatingView.as_view(),         name='rating-submit'),
    path('mine/',                             MyRatingsView.as_view(),            name='rating-mine'),
    path('ranking/',                          AllDriversRankingView.as_view(),    name='rating-ranking'),
    path('driver/<int:driver_id>/',           DriverRatingsListView.as_view(),    name='rating-driver-list'),
    path('driver/<int:driver_id>/average/',   DriverAverageRatingView.as_view(),  name='rating-driver-avg'),
]