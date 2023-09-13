from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from .serializers import UserRegistrationSerializer
from rest_framework.response import Response
from django.contrib.auth.models import User
from rest_framework.views import APIView
from django.core.cache import cache
from django.db.models import Count
from rest_framework import status
from django.db import transaction
from django.http import Http404
from dotenv import load_dotenv
from .serializers import *
import requests
import os

load_dotenv()


class UserRegistrationView(APIView):
    def post(self, request):
        """
        Handle POST requests for user registration and token generation.

        This method receives a POST request with user registration data in the request data.
        It validates the data using the UserRegistrationSerializer and creates a new user
        account if the data is valid. Then, it generates a refresh and access token for the
        new user and returns the access token in the response.

        Args:
            request (HttpRequest): The HTTP request object containing user registration data.

        Returns:
            Response: A Response object with the access token if registration is successful,
            or validation errors if the data is invalid.
        """
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            # Create a new user account with the provided data
            user = User.objects.create_user(
                username=serializer.validated_data["username"],
                password=serializer.validated_data["password"],
            )

            # Generate a refresh and access token for the user
            refresh = RefreshToken.for_user(user)
            return Response(
                {"access_token": str(refresh.access_token)},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExternalMoviesAPI(APIView):
    """
    This API view is responsible for making authenticated GET requests to an external movie API.

    It requires authentication credentials (username and password) to access the API.
    The API endpoint URL is retrieved from environment variables.

    Usage:
    1. Ensure that the 'API_URL', 'ACCOUNT', and 'PASSWORD' environment variables are set.
    2. Use an authenticated GET request to fetch data from the external API.
    3. If the request is successful (HTTP status code 200), it returns the API response data.
    4. If an error occurs (e.g., authentication failure or API unavailable), it returns an error message.

    Permissions:
    - Users must be authenticated to access this API view.

    Example:
    To access movie data, make a GET request to this endpoint after setting the required environment variables.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Define the API endpoint and authentication credentials
        api_url = os.getenv("API_URL", None)
        username = os.getenv("ACCOUNT", None)
        password = os.getenv("PASSWORD", None)
        # Make a GET request to the external API with authentication
        response = requests.get(api_url, auth=(username, password))
        # Check if the request was successful (HTTP status code 200)
        if response.status_code == 200:
            data = response.json()
            return Response(data)
        else:
            # Handle errors, e.g., authentication failure or API unavailable
            return Response(
                {"message": "Error fetching data from the external API"},
                status=response.status_code,
            )


class CollectionView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, uuid, user):
        """
        Retrieve a Collection object based on the provided UUID and user.
        Args:
            uuid (str): The UUID of the Collection object.
            user (User): The user associated with the Collection object.
        Returns:
            Collection: The retrieved Collection object.
        Raises:
            Http404: If the Collection object does not exist.
        """
        try:
            return Collection.objects.get(user=user, uuid=uuid)
        except Collection.DoesNotExist:
            raise Http404

    def calculate_favorite_genres(self, user):
        """
        Calculate the top 3 favorite genres based on the movies in the user's collections.
        Args:
            user (User): The user for whom to calculate the favorite genres.
        Returns:
            str: A comma-separated string of the top 3 favorite genres.
        """
        # Calculate the top 3 favorite genres based on the movies in user's collections
        favorite_genres = (
            Collection.objects.filter(user=user)
            .values("movies__genres")
            .annotate(
                genre_count=Count("movies__genres"),
            )
            .order_by("-genre_count")[:3]
        )
        # Extract the genres from the query result
        favorite_genres_list = [genre["movies__genres"]
                                for genre in favorite_genres]
        return ", ".join(favorite_genres_list)

    def get(self, request, collection_uuid=None):
        """
        Retrieve a specific collection or all collections for the authenticated user.
        Args:
            request (HttpRequest): The HTTP request object.
            collection_uuid (str, optional): The UUID of the specific collection to retrieve.
        Returns:
            Response: The HTTP response containing the collection(s) data.
        """
        if collection_uuid:
            collection = self.get_object(
                user=request.user.id, uuid=collection_uuid)
            serializer = CollectionSerializer(collection).data
            return Response(serializer, status=status.HTTP_200_OK)
        collections = Collection.objects.filter(
            user=request.user.id,
        ).values("title", "uuid", "description")
        favorite_genres = self.calculate_favorite_genres(request.user)
        response_data = {
            "is_success": True,
            "data": {
                "collections": collections,
                "favourite_genres": favorite_genres,
            },
        }
        return Response(response_data, status=status.HTTP_200_OK)

    @transaction.atomic
    def post(self, request):
        """
        Create a new collection for the authenticated user.
        Args:
            request (HttpRequest): The HTTP request object.
        Returns:
            Response: The HTTP response indicating the success of the collection creation.
        """
        data = request.data
        movie_data = data.pop("movies", [])
        data["user"] = request.user.id
        serializer = CollectionSerializer(data=data)
        if serializer.is_valid():
            collection = serializer.save()
            # Process the movie data and add movies to the collection
            for movie_info in movie_data:
                # Create a movie serializer instance with the movie data
                movie_serializer = MovieSerializer(data=movie_info)
                movie_serializer.is_valid(raise_exception=True)
                # Get or create the movie object based on the UUID
                movie, _ = Movie.objects.get_or_create(
                    uuid=movie_info["uuid"],
                    defaults=movie_serializer.validated_data,
                )
                # Add the movie to the collection
                collection.movies.add(movie)
            return Response(
                {"collection_uuid": collection.uuid},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @transaction.atomic
    def put(self, request, collection_uuid):
        """
        Update an existing collection for the authenticated user.
        Args:
            request (HttpRequest): The HTTP request object.
            collection_uuid (str): The UUID of the collection to update.
        Returns:
            Response: The HTTP response indicating the success of the collection update.
        """
        collection = self.get_object(
            user=request.user.id, uuid=collection_uuid)
        data = request.data
        # Update the collection's title and description if provided
        if "title" in data:
            collection.title = data["title"]
        if "description" in data:
            collection.description = data["description"]
        # Update the collection's movies list if provided
        if "movies" in data:
            updated_movies = []
            for movie_info in data["movies"]:
                # Create a movie serializer instance with the movie data
                movie_serializer = MovieSerializer(data=movie_info)
                movie_serializer.is_valid(raise_exception=True)
                # Get or create the movie object based on the UUID
                movie, _ = Movie.objects.get_or_create(
                    uuid=movie_info["uuid"],
                    defaults=movie_serializer.validated_data,
                )
                updated_movies.append(movie)
            # Set the updated movies list for the collection
            collection.movies.set(updated_movies)
        collection.save()
        return Response({"message": "Collection has been updated"}, status=status.HTTP_200_OK)

    def delete(self, request, collection_uuid):
        """
        Delete a specific collection for the authenticated user.
        Args:
            request (HttpRequest): The HTTP request object.
            collection_uuid (uuid): The UUID of the collection to delete.
        Returns:
            Response: The HTTP response indicating the success of the deletion.
        """
        collection = self.get_object(
            user=request.user.id, uuid=collection_uuid)
        collection.delete()
        return Response({"message": "Collection has been deleted"}, status=status.HTTP_200_OK)


class RequestCountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Handle GET requests to retrieve the current request count from the cache.
        :param request: The HTTP request object.
        :return: A Response object containing the current request count.
        """
        # Retrieve the current request count from the cache, defaulting to 0 if not found.
        request_count = cache.get("request_count", default=0)
        return Response({"requests": request_count}, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Handle POST requests to reset the request count in the cache.
        :param request: The HTTP request object.
        :return: A Response object confirming the request count reset.
        """
        # Check if the request count key exists in the cache.
        if cache.get("request_count"):
            # If it exists, set the request count to 0 to reset it.
            cache.set("request_count", 0, None)
        return Response({"message": "Request count reset successfully"}, status=status.HTTP_200_OK)
