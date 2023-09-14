from rest_framework.test import APITestCase, APIClient
from .models import Collection, Movie
from django.core.cache import cache
from rest_framework import status
from django.urls import reverse
from .factories import *


class UserRegistrationViewTest(APITestCase):
    def test_user_registration(self):
        user_data = {
            "username": "testuser",
            "password": "testpassword",
        }
        url = reverse("register")
        response = self.client.post(url, user_data, format="json")
        # Assert that the response status code is HTTP 201 Created
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Assert that the access_token key is present in the response JSON
        self.assertIn("access_token", response.data)


class RequestCountViewTest(APITestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_request_count(self):
        # Ensure a GET request to retrieve the request count works
        url = reverse("request-count")
        cache.set("request_count", 5, None)
        response = self.client.get(url)
        # Assert that the response status code is HTTP 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["requests"], 5+1)

    def test_request_count_reset(self):
        # Ensure a POST request to reset the request count works
        url = reverse("request-count-reset")
        # Set a test value in the cache to simulate a request count
        cache.set("request_count", 10, None)
        response = self.client.post(url)
        # Assert that the response status code is HTTP 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(cache.get("request_count"), 0)


class ExternalMoviesAPITest(APITestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_external_movie_api(self):
        # Ensure a GET request to get all movies from external api
        url = reverse("movies-get")
        response = self.client.get(url)
        # Assert that the response status code is HTTP 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)


class CollectionPostGetViewTest(APITestCase):
    def setUp(self):
        # Create a user for authentication
        self.user = UserFactory()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.url = reverse("collections")

    def test_get_all_collection(self):
        # Create a test collection using Factory Boy
        CollectionFactory.create_batch(5, user=self.user)
        response = self.client.get(self.url)
        # Assert that the response status code is HTTP 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["is_success"], True)

    def test_create_collection_with_movies(self):
        # Define the data for creating a collection with movies
        collection_data = {
            "title": "My Collection",
            "description": "A collection of great movies",
            "movies": [
                {
                    "title": "Queerama",
                    "description": "50 years after decriminalisation of homosexuality in the UK, director Daisy Asquith mines the jewels of the BFI archive to take us into the relationships, desires, fears and expressions of gay men and women in the 20th century.",
                    "genres": "",
                    "uuid": "57baf4f4-c9ef-4197-9e4f-acf04eae5b4d"
                },
                {
                    "title": "Robin Hood",
                    "description": "Yet another version of the classic epic, with enough variation to make it interesting. The story is the same, but some of the characters are quite different from the usual, in particular Uma Thurman's very special maid Marian. The photography is also great, giving the story a somewhat darker tone.",
                    "genres": "Drama,Action,Romance",
                    "uuid": "73399935-2165-41f0-a6a4-1336ef5e5c20"
                },
            ],
        }

        response = self.client.post(self.url, collection_data, format="json")
        # Assert that the response status code is HTTP 201 Created
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Collection.objects.count(), 1)
        self.assertEqual(Movie.objects.count(), 2)

        created_collection = Collection.objects.first()
        self.assertEquals(created_collection.uuid,
                          response.data["collection_uuid"])
        self.assertEqual(created_collection.movies.count(), 2)
        self.assertEqual(created_collection.title, "My Collection")

    def test_create_collection_without_movies(self):
        # Define the data for creating a collection without movies
        collection_data = {
            "title": "My Collection",
            "description": "A collection of great movies",
            "movies": [],  # Empty list of movies
        }
        response = self.client.post(self.url, collection_data, format="json")
        # Assert that the response status code is HTTP 201 Created
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Collection.objects.count(), 1)
        self.assertEqual(Collection.objects.first().title, "My Collection")

    def test_create_collection_invalid_data(self):
        invalid_data = {
            "title": "My Collection",
            # Missing "description" field
            "movies": [],
        }
        response = self.client.post(self.url, invalid_data, format="json")
        # Assert that the response status code is HTTP 400 Bad Request
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CollectionViewTest(APITestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_get_specific_collection(self):
        # Create a test collection using Factory Boy
        collection = CollectionFactory(user=self.user)
        url = reverse("collections-get-put", args=[collection.uuid])
        response = self.client.get(url)

        # Assert that the response status code is HTTP 200 and also based on title
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("title", response.data)

    def test_delete_collection(self):
        # Create a collection using the factory
        collection = CollectionFactory(user=self.user)
        url = reverse("collections-get-put", args=[collection.uuid])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Assert that the collection has been deleted from the database
        self.assertFalse(Collection.objects.filter(
            uuid=collection.uuid).exists())
        # Additional assertions based on your requirements
        self.assertEqual(response.data["message"],
                         "Collection has been deleted")

    def test_update_collection(self):
        # Create a collection and movies using the factories
        collection = CollectionFactory(user=self.user)
        movie1 = MovieFactory()
        movie2 = MovieFactory()

        # Define the data for updating the collection
        updated_data = {
            "title": "Updated Collection",
            "description": "Updated description",
            "movies": [
                {
                    "title": movie1.title,
                    "description": movie1.description,
                    "genres": movie1.genres,
                    "uuid": str(movie1.uuid),
                },
                {
                    "title": movie2.title,
                    "description": movie2.description,
                    "genres": movie2.genres,
                    "uuid": str(movie2.uuid),
                },
            ],
        }

        url = reverse("collections-get-put", args=[collection.uuid])
        response = self.client.put(url, updated_data, format="json")
        # Assert that the response status code is HTTP 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Refresh the collection from the database
        collection.refresh_from_db()
        self.assertEqual(collection.title, "Updated Collection")
        self.assertEqual(collection.description, "Updated description")
        self.assertEqual(collection.movies.count(), 2)
        self.assertEqual(response.data["message"],
                         "Collection has been updated")
