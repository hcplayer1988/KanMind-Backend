"""Admin configuration for board app."""

from django.contrib import admin

from .models import Board


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    """Admin interface for Board model."""

    list_display = ['title', 'owner', 'created_at']
    filter_horizontal = ['members']