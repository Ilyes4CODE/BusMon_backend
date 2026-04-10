from django.urls import path
from .views import (
    NotificationListView,
    UnreadCountView,
    MarkReadView,
    MarkAllReadView,
    DeleteNotificationView,
    SendNotificationView,
    NotificationStatsView,
)

urlpatterns = [
    path('',                    NotificationListView.as_view(),   name='notification-list'),
    path('send/',               SendNotificationView.as_view(),   name='notification-send'),
    path('mark-all-read/',      MarkAllReadView.as_view(),        name='notification-mark-all'),
    path('unread-count/',       UnreadCountView.as_view(),        name='notification-unread'),
    path('stats/',              NotificationStatsView.as_view(),  name='notification-stats'),
    path('<int:pk>/read/',      MarkReadView.as_view(),           name='notification-read'),
    path('<int:pk>/delete/',    DeleteNotificationView.as_view(), name='notification-delete'),
]