from django.contrib.auth.models import User
from django.db import models
import uuid


class Movie(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    genres = models.CharField(max_length=255, blank=True)
    uuid = models.UUIDField(unique=True, editable=False)

    def __str__(self):
        return str(self.uuid)


class Collection(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    movies = models.ManyToManyField(Movie, related_name="collections")
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="user_collections")
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        return str(self.uuid)
