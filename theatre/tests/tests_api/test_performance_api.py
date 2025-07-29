from datetime import datetime

from django.contrib.auth import get_user_model
from django.db.models import F, Count
from django.test import TestCase
from django.urls import reverse
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware
from rest_framework import status

from rest_framework.test import APIClient
from theatre.models import Performance
from theatre.serializers import (
    PerformanceListSerializer,
    PerformanceRetrieveSerializer
)
from theatre.tests.test_models import create_theatre_hall
from theatre.tests.tests_api.test_helpers import (
    create_performance,
    create_play
)

PERFORMANCE_URL = reverse("theatre:performance-list")


def performance_detail_url(performance_id):
    return reverse("theatre:performance-detail", args=[performance_id])


def get_performance_queryset():
    return Performance.objects.select_related("play", "theatre_hall").annotate(
        tickets_available=(
            F("theatre_hall__rows") * F("theatre_hall__seats_in_row")
            - Count("tickets")
        )
    )


class PublicPerformanceApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_theatre_list_auth_required(self):
        response = self.client.get(PERFORMANCE_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_theatre_detail_auth_required(self):
        performance = create_performance()
        response = self.client.get(performance_detail_url(performance.id))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivatePerformanceApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="user@test.com", password="test_password"
        )
        self.client.force_authenticate(self.user)

    def test_performance_list(self):
        create_performance()
        create_performance(show_time="2025-07-28 20:00:00")
        response = self.client.get(PERFORMANCE_URL)

        performances = get_performance_queryset()

        serializer = PerformanceListSerializer(performances, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], serializer.data)

    def test_filter_performance_by_date(self):
        performance_1 = create_performance(show_time="2025-07-30 15:00:00")
        performance_2 = create_performance()
        response = self.client.get(PERFORMANCE_URL, {"date": "2025-07-30"})

        performances = get_performance_queryset()
        serializer_1 = PerformanceListSerializer(
            performances.filter(id=performance_1.id), many=True
        )
        serializer_2 = PerformanceListSerializer(
            performances.filter(id=performance_2.id), many=True
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(serializer_1.data[0], response.data["results"])
        self.assertNotIn(serializer_2.data[0], response.data["results"])

    def test_filter_performance_by_play(self):
        play_1 = create_play(title="Test Title 1")
        performance_1 = create_performance(play=play_1)
        performance_2 = create_performance()
        response = self.client.get(PERFORMANCE_URL, {"play": f"{play_1.id}"})

        performances = get_performance_queryset()
        serializer_1 = PerformanceListSerializer(
            performances.filter(id=performance_1.id), many=True
        )
        serializer_2 = PerformanceListSerializer(
            performances.filter(id=performance_2.id), many=True
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(serializer_1.data[0], response.data["results"])
        self.assertNotIn(serializer_2.data[0], response.data["results"])

    def test_performance_detail(self):
        performance = create_performance(show_time="2025-07-30 15:00:00")
        url = performance_detail_url(performance.id)
        response = self.client.get(url)
        serializer = PerformanceRetrieveSerializer(performance)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(serializer.data, response.data)

    def test_create_performance_forbidden(self):
        show_time = make_aware(datetime(2025, 7, 25, 20, 0, 0))
        play = create_play()
        theatre_hall = create_theatre_hall()
        payload = {
            "show_time": show_time,
            "play": play,
            "theatre_hall": theatre_hall,
        }
        response = self.client.post(PERFORMANCE_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_put_performance_forbidden(self):
        performance = create_performance()
        url = performance_detail_url(performance.id)
        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_performance_forbidden(self):
        performance = create_performance()
        url = performance_detail_url(performance.id)
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_performance_forbidden(self):
        performance = create_performance()
        url = performance_detail_url(performance.id)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminPerformanceApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_superuser(
            email="admin@test.com", password="test_password"
        )
        self.client.force_authenticate(self.user)

    def test_create_performance(self):
        show_time = make_aware(datetime(2025, 7, 25, 20, 0, 0))
        play = create_play()
        theatre_hall = create_theatre_hall()
        payload = {
            "play": play.id,
            "theatre_hall": theatre_hall.id,
            "show_time": show_time,
        }
        response = self.client.post(PERFORMANCE_URL, payload)
        performance = Performance.objects.get(id=response.data["id"])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            payload["show_time"], getattr(performance, "show_time")
        )
        self.assertEqual(payload["play"], getattr(performance, "play_id"))
        self.assertEqual(
            payload["theatre_hall"], getattr(performance, "theatre_hall_id")
        )

    def test_patch_performance(self):
        performance = create_performance()
        url = performance_detail_url(performance.id)

        payload = {"show_time": "2025-08-01T18:00:00Z"}
        response = self.client.patch(url, payload, format="json")
        performance.refresh_from_db()
        expected = parse_datetime(payload["show_time"])

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(performance.show_time, expected)

    def test_put_performance(self):
        performance = create_performance()
        url = performance_detail_url(performance.id)

        new_play = create_play(title="Test Play")
        new_theatre_hall = create_theatre_hall(name="Test Theatre Hall")
        payload = {
            "play": new_play.id,
            "theatre_hall": new_theatre_hall.id,
            "show_time": "2025-08-01T18:00:00Z",
        }
        response = self.client.put(url, payload, format="json")
        performance.refresh_from_db()
        expected_show_time = parse_datetime(payload["show_time"])

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(performance.show_time, expected_show_time)
        self.assertEqual(payload["play"], new_play.id)
        self.assertEqual(payload["theatre_hall"], new_theatre_hall.id)

    def test_delete_performance(self):
        performance = create_performance()
        url = performance_detail_url(performance.id)
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Performance.objects.filter(
            id=performance.id).exists()
        )
