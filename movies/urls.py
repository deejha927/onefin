from django.urls import path
from .views import *

urlpatterns = [
    path("register/", UserRegistrationView.as_view(), name="register"),
    path("movies/", ExternalMoviesAPI.as_view(), name="movies-get"),
    path("request-count/", RequestCountView.as_view(), name="request-count"),
    path("request-count/reset/", RequestCountView.as_view(), name="request-count-reset"),
]
