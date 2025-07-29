from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from theatre.models import Reservation
from theatre.serializers import (
    ReservationSerializer,
    ReservationListSerializer
)
from theatre.tests.tests_api.test_helpers import (
    create_ticket,
    create_performance
)

RESERVATION_URL = reverse("theatre:reservation-list")


class PublicReservationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(RESERVATION_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateReservationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="user@test.com", password="test_password"
        )
        self.client.force_authenticate(self.user)

    def test_reservation_list(self):
        reservation = Reservation.objects.create(user=self.user)
        create_ticket(reservation=reservation)
        response = self.client.get(RESERVATION_URL)
        reservations = Reservation.objects.all()
        serializer = ReservationListSerializer(reservations, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertIn(serializer.data[0], response.data["results"])

    def test_create_reservation_with_tickets(self):
        performance = create_performance()
        tickets = [
            {"row": 5, "seat": 5, "performance": performance.id},
            {"row": 5, "seat": 6, "performance": performance.id},
        ]
        response = self.client.post(
            RESERVATION_URL,
            {"tickets": tickets},
            format="json"
        )
        reservation = Reservation.objects.get(id=response.data["id"])
        serializer = ReservationSerializer(reservation)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, serializer.data)

    def test_create_reservation_without_tickets(self):
        response = self.client.post(
            RESERVATION_URL,
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_reservation_with_invalid_seat_row(self):
        performance = create_performance()
        ticket_1 = [
            {"row": 0, "seat": 21, "performance": performance.id},
        ]
        ticket_2 = [
            {"row": 21, "seat": 0, "performance": performance.id},
        ]
        response_1 = self.client.post(
            RESERVATION_URL,
            {"tickets": ticket_1},
            format="json"
        )
        response_2 = self.client.post(
            RESERVATION_URL,
            {"tickets": ticket_2},
            format="json"
        )

        self.assertEqual(response_1.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_2.status_code, status.HTTP_400_BAD_REQUEST)
