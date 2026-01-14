"""URL configuration for core project."""

from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('authentikation.api.urls')),
    path('api/', include('board.api.urls')),
    path('api/', include('tasks.api.urls')),
]

