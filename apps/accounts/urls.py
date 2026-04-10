from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    CustomTokenObtainPairView,
    RegisterView,
    LogoutView,
    ProfileView,
    ChangePasswordView,
    UserListView,
    UserDetailView,
)

urlpatterns = [
    path('register/',        RegisterView.as_view(),              name='auth-register'),
    path('login/',           CustomTokenObtainPairView.as_view(), name='auth-login'),
    path('token/refresh/',   TokenRefreshView.as_view(),          name='auth-token-refresh'),
    path('logout/',          LogoutView.as_view(),                name='auth-logout'),
    path('profile/',         ProfileView.as_view(),               name='auth-profile'),
    path('change-password/', ChangePasswordView.as_view(),        name='auth-change-password'),
    path('users/',           UserListView.as_view(),              name='user-list'),
    path('users/<int:pk>/',  UserDetailView.as_view(),            name='user-detail'),
]