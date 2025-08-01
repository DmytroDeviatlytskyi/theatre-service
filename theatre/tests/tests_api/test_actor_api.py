from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from theatre.models import Actor
from theatre.serializers import ActorSerializer
from theatre.tests.tests_api.test_helpers import create_actor


ACTOR_URL = reverse("theatre:actor-list")


class PublicActorApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(ACTOR_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateActorApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="user@test.com", password="test_password"
        )
        self.client.force_authenticate(self.user)

    def test_actor_list(self):
        create_actor()
        create_actor(last_name="Carver")
        response = self.client.get(ACTOR_URL)
        actors = Actor.objects.all()
        serializer = ActorSerializer(actors, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(actors.count(), 2)
        self.assertEqual(response.data["results"], serializer.data)

    def test_create_actor_forbidden(self):
        payload = {
            "first_name": "Test first name",
            "last_name": "Test last name",
        }
        response = self.client.post(ACTOR_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminActorApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_superuser(
            email="admin@test.com", password="test_password"
        )
        self.client.force_authenticate(self.user)

    def test_create_actor(self):
        payload = {
            "first_name": "Test first name",
            "last_name": "Test last name",
        }
        response = self.client.post(ACTOR_URL, payload)
        actor = Actor.objects.get(id=response.data["id"])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(payload["first_name"], getattr(actor, "first_name"))
        self.assertEqual(payload["last_name"], getattr(actor, "last_name"))
