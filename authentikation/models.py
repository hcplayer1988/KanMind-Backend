from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

class CustomUser(AbstractUser):
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
        return self.email