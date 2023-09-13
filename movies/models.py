from django.contrib.auth.models import User
from django.db import models


class Movie(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    genres = models.CharField(max_length=255, blank=True)
    uuid = models.UUIDField(unique=True)


class Collection(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    movies = models.ManyToManyField(Movie, related_name="collections")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_collections")
    collection_uuid = models.UUIDField(unique=True)
