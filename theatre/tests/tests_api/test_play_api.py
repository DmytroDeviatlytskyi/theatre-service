import os
import tempfile

from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from theatre.models import Play
from theatre.serializers import PlayListSerializer, PlayRetrieveSerializer
from theatre.tests.tests_api.test_helpers import (
    create_play,
    create_genre,
    create_actor,
    create_performance
)

PLAY_URL = reverse("theatre:play-list")
PERFORMANCE_URL = reverse("theatre:performance-list")


def image_upload_url(play_id):
    return reverse("theatre:play-upload-image", args=[play_id])


def play_detail_url(play_id):
    return reverse("theatre:play-detail", args=[play_id])


class PlayImageUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_superuser(
            "admin@test.com", "password"
        )
        self.client.force_authenticate(user=self.user)
        self.play = create_play()
        self.genre = create_genre()
        self.actor = create_actor()
        self.performance = create_performance(play=self.play)

    def tearDown(self):
        self.play.image.delete()

    def test_play_upload_image(self):
        url = image_upload_url(self.play.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as tmp:
            img = Image.new("RGB", (10, 10))
            img.save(tmp, format="JPEG")
            tmp.seek(0)
            response = self.client.post(
                url,
                {"image": tmp},
                format="multipart"
            )
        self.play.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("image", response.data)
        self.assertTrue(os.path.exists(self.play.image.path))

    def test_upload_image_bad_request(self):
        url = image_upload_url(self.play.id)
        response = self.client.post(
            url,
            {"image": "not image"},
            format="multipart"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_image_to_play_list(self):
        url = PLAY_URL
        with tempfile.NamedTemporaryFile(suffix=".jpg") as tmp:
            img = Image.new("RGB", (10, 10))
            img.save(tmp, format="JPEG")
            tmp.seek(0)
            response = self.client.post(
                url,
                {
                    "title": "Test Title",
                    "description": "Test description",
                    "genres": [1],
                    "actors": [1],
                    "image": tmp
                },
                format="multipart",
            )
        play = Play.objects.get(title="Test Title")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(play.image)

    def test_image_is_shown_on_play_detail(self):
        url = image_upload_url(self.play.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as tmp:
            img = Image.new("RGB", (10, 10))
            img.save(tmp, format="JPEG")
            tmp.seek(0)
            self.client.post(url, {"image": tmp}, format="multipart")
        response = self.client.get(play_detail_url(self.play.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("image", response.data)

    def test_image_is_shown_on_play_list(self):
        url = image_upload_url(self.play.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as tmp:
            img = Image.new("RGB", (10, 10))
            img.save(tmp, format="JPEG")
            tmp.seek(0)
            self.client.post(url, {"image": tmp}, format="multipart")
        response = self.client.get(PLAY_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("image", response.data["results"][0].keys())

    def test_image_is_shown_on_performance_detail(self):
        url = image_upload_url(self.play.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as tmp:
            img = Image.new("RGB", (10, 10))
            img.save(tmp, format="JPEG")
            tmp.seek(0)
            self.client.post(url, {"image": tmp}, format="multipart")
        response = self.client.get(PERFORMANCE_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("play_image", response.data["results"][0].keys())


class PublicPlayApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(PLAY_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivatePlayApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "user@test.com", "test_password"
        )
        self.client.force_authenticate(self.user)

    def test_play_list(self):
        play = create_play()
        genre = create_genre()
        actor = create_actor()
        play.genres.add(genre)
        play.actors.add(actor)
        play.save()

        response = self.client.get(PLAY_URL)
        plays = Play.objects.all()
        serializer = PlayListSerializer(plays, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], serializer.data)

    def test_filter_play_by_actors(self):
        play_without_actor = create_play()
        play_with_actor_1 = create_play(title="Test Title 1")
        play_with_actor_2 = create_play(title="Test Title 2")

        actor_1 = create_actor(first_name="John", last_name="Thorne")
        actor_2 = create_actor(first_name="Liam", last_name="Blackwell")

        play_with_actor_1.actors.add(actor_1)
        play_with_actor_2.actors.add(actor_2)

        response = self.client.get(
            PLAY_URL, {"actors": f"{actor_1.id}, {actor_2.id}"}
        )

        serializer_without_actor = PlayListSerializer(play_without_actor)
        serializer_with_actor_1 = PlayListSerializer(play_with_actor_1)
        serializer_with_actor_2 = PlayListSerializer(play_with_actor_2)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn(
            serializer_without_actor.data, response.data["results"]
        )
        self.assertIn(serializer_with_actor_1.data, response.data["results"])
        self.assertIn(serializer_with_actor_2.data, response.data["results"])

    def test_filter_play_by_genres(self):
        play_without_genre = create_play()
        play_with_genre_1 = create_play(title="Test Title 1")
        play_with_genre_2 = create_play(title="Test Title 2")

        genre_1 = create_genre(name="Drama")
        genre_2 = create_genre(name="Romantic")

        play_with_genre_1.genres.add(genre_1)
        play_with_genre_2.genres.add(genre_2)

        response = self.client.get(
            PLAY_URL, {"genres": f"{genre_1.id}, {genre_2.id}"}
        )

        serializer_without_genre = PlayListSerializer(play_without_genre)
        serializer_with_genre_1 = PlayListSerializer(play_with_genre_1)
        serializer_with_genre_2 = PlayListSerializer(play_with_genre_2)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn(
            serializer_without_genre.data, response.data["results"]
        )
        self.assertIn(serializer_with_genre_1.data, response.data["results"])
        self.assertIn(serializer_with_genre_2.data, response.data["results"])

    def test_filter_play_by_title(self):
        play_1 = create_play(title="Test Title 1")
        play_2 = create_play(title="Test Title 2")

        response = self.client.get(PLAY_URL, {"title": "Test Title 1"})

        serializer_play_1 = PlayListSerializer(play_1)
        serializer_play_2 = PlayListSerializer(play_2)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(serializer_play_1.data, response.data["results"])
        self.assertNotIn(serializer_play_2.data, response.data["results"])

    def test_play_detail(self):
        play = create_play()
        play.actors.add(create_actor())
        play.genres.add(create_genre())

        url = play_detail_url(play.id)
        response = self.client.get(url)
        serializer = PlayRetrieveSerializer(play)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(serializer.data, response.data)

    def test_create_play_forbidden(self):
        payload = {
            "title": "Test Title 1",
            "description": "Test Description 1",
        }
        response = self.client.post(PLAY_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminPlayApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_superuser(
            email="admin@test.com", password="test_password", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_play(self):
        genre = create_genre()
        actor = create_actor()
        payload = {
            "title": "Test Title 1",
            "description": "Test Description 1",
            "genres": [genre.id],
            "actors": [actor.id],
        }
        response = self.client.post(PLAY_URL, payload)
        play = Play.objects.get(id=response.data["id"])
        actors = play.actors.all()
        genres = play.genres.all()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(payload["title"], getattr(play, "title"))
        self.assertEqual(payload["description"], getattr(play, "description"))
        self.assertIn(genre, genres)
        self.assertIn(actor, actors)

    def test_delete_play_not_allowed(self):
        play = create_play()
        url = play_detail_url(play.id)
        response = self.client.delete(url)

        self.assertEqual(
            response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def test_put_play_not_allowed(self):
        play = create_play()
        url = play_detail_url(play.id)
        response = self.client.put(url)

        self.assertEqual(
            response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def test_patch_play_not_allowed(self):
        play = create_play()
        url = play_detail_url(play.id)
        response = self.client.patch(url)

        self.assertEqual(
            response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED
        )
