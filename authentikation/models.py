"""Custom user model for authentication."""

from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models


class CustomUser(AbstractUser):
    """
    Custom user model that uses email as the primary identifier.
    Username field allows spaces and special characters.
    """

    email = models.EmailField(unique=True)

    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[],
        help_text='Required. 150 characters or fewer.',
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        """Return email as string representation."""
        return self.email