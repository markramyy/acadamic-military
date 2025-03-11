from django.contrib.auth.models import AbstractUser
from core.models import BaseModel


class User(AbstractUser, BaseModel):
    """Custom user model"""
    pass
