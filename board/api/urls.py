"""URL configuration for board API endpoints."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import BoardViewSet

router = DefaultRouter()
router.register(r'boards', BoardViewSet, basename='board')

urlpatterns = [
    path('', include(router.urls)),
]

