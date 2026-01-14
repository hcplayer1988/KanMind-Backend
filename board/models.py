"""Models for board app."""

from django.conf import settings
from django.db import models


class Board(models.Model):
    """Board model for organizing tasks with multiple members."""

    title = models.CharField(max_length=255)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_boards'
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='boards',
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """Return board title as string representation."""
        return self.title

    class Meta:
        ordering = ['-created_at']
        
