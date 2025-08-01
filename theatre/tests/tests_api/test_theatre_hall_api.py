from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from theatre.models import TheatreHall
from theatre.serializers import TheatreHallSerializer
from theatre.tests.tests_api.test_helpers import create_theatre_hall


THEATRE_HALL_URL = reverse("theatre:theatrehall-list")


class PublicTheatreHallApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(THEATRE_HALL_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTheatreHallApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="user@test.com", password="test_password"
        )
        self.client.force_authenticate(self.user)

    def test_theatre_hall_list(self):
        create_theatre_hall()
        create_theatre_hall(name="New Hall")
        response = self.client.get(THEATRE_HALL_URL)
        theatre_halls = TheatreHall.objects.all()
        serializer = TheatreHallSerializer(theatre_halls, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], serializer.data)
        self.assertEqual(response.data["count"], theatre_halls.count())

    def test_create_theatre_hall_forbidden(self):
        payload = {"name": "Test Hall"}
        response = self.client.post(THEATRE_HALL_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminTheatreHallApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_superuser(
            email="admin@test.com", password="test_password"
        )
        self.client.force_authenticate(self.user)

    def test_create_theatre_hall(self):
        payload = {
            "name": "New Hall",
            "rows": 20,
            "seats_in_row": 20
        }
        response = self.client.post(THEATRE_HALL_URL, payload)
        theatre_hall = TheatreHall.objects.get(id=response.data["id"])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(payload["name"], getattr(theatre_hall, "name"))
