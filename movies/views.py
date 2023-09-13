from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from .serializers import UserRegistrationSerializer
from rest_framework.response import Response
from django.contrib.auth.models import User
from rest_framework.views import APIView
from django.core.cache import cache
from rest_framework import status
from dotenv import load_dotenv
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
