from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from theatre.models import Genre
from theatre.serializers import GenreSerializer
from theatre.tests.tests_api.test_helpers import create_genre

GENRE_URL = reverse("theatre:genre-list")


class PublicGenreApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(GENRE_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateGenreApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="user@test.com", password="test+password"
        )
        self.client.force_authenticate(self.user)

    def test_genre_list(self):
        create_genre()
        create_genre(name="Drama")
        response = self.client.get(GENRE_URL)
        genres = Genre.objects.all()
        serializer = GenreSerializer(genres, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], serializer.data)
        self.assertEqual(genres.count(), 2)

    def test_create_genre_forbidden(self):
        payload = {"name": "Drama"}
        response = self.client.post(GENRE_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminGenreApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_superuser(
            email="admin@test.com", password="test_password"
        )
        self.client.force_authenticate(self.user)

    def test_create_genre(self):
        payload = {
            "name": "Drama"
        }
        response = self.client.post(GENRE_URL, payload)
        genre = Genre.objects.get(id=response.data["id"])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(payload["name"], getattr(genre, "name"))
