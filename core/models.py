from django.db import models


class BaseModel(models.Model):
    """Base model for all other models to inherit from"""
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
