from django.db import models
from core.models import BaseModel


class Faculty(BaseModel):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.name
