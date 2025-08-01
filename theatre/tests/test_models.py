from django.contrib.auth import get_user_model
from django.test import TestCase
from django.core.exceptions import ValidationError

from theatre.models import (
    Actor,
    Genre,
    TheatreHall,
    Play,
    Performance,
    Reservation,
    Ticket
)


def create_user(**kwargs):
    payload = {
        "email": "user@test.com", "password": "teat_password",
    }
    payload.update(**kwargs)
    return get_user_model().objects.create_user(**payload)


def create_actor(**kwargs):
    payload = {"first_name": "John", "last_name": "Thorne"}
    payload.update(**kwargs)
    return Actor.objects.create(**payload)


def create_genre(**kwargs):
    payload = {"name": "Drama"}
    payload.update(**kwargs)
    return Genre.objects.create(**payload)


def create_theatre_hall(**kwargs):
    payload = {
        "name": "Theatre Hall",
        "rows": 20,
        "seats_in_row": 20
    }
    payload.update(**kwargs)
    return TheatreHall.objects.create(**payload)


def create_play(**kwargs):
    genres = create_genre()
    actors = create_actor()
    payload = {
        "title": "Play",
        "description": "Description",
    }
    payload.update(**kwargs)
    play = Play.objects.create(**payload)
    play.genres.add(genres)
    play.actors.add(actors)
    play.save()
    return play


def create_performance(**kwargs):
    play = create_play()
    theatre_hall = create_theatre_hall()
    payload = {
        "play": play,
        "theatre_hall": theatre_hall,
        "show_time": "2025-07-28 20:00:00",
    }
    payload.update(**kwargs)
    return Performance.objects.create(**payload)


class ActorModelTests(TestCase):
    def setUp(self):
        self.actor = create_actor()

    def test_create_actor(self):
        actor_2 = create_actor(first_name="Sophie", last_name="Winters")
        actors = Actor.objects.all()

        self.assertEqual(actors.count(), 2)
        self.assertIn(self.actor, actors)
        self.assertIn(actor_2, actors)

    def test_actor_str(self):
        self.assertEqual(str(self.actor), "John Thorne")


class GenreModelTests(TestCase):
    def setUp(self):
        self.genre = create_genre()

    def test_create_genre(self):
        genre_2 = create_genre(name="Comedy")
        genres = Genre.objects.all()

        self.assertEqual(genres.count(), 2)
        self.assertIn(self.genre, genres)
        self.assertIn(genre_2, genres)

    def test_genre_str(self):
        self.assertEqual(str(self.genre), "Drama")


class TheatreHallModelTests(TestCase):
    def setUp(self):
        self.theatre_hall = create_theatre_hall()

    def test_create_theatre_hall(self):
        theatre_hall_2 = create_theatre_hall(
            name="Test Hall",
            rows=20,
            seats_in_row=15
        )
        theatre_halls = TheatreHall.objects.all()

        self.assertEqual(theatre_halls.count(), 2)
        self.assertIn(self.theatre_hall, theatre_halls)
        self.assertIn(theatre_hall_2, theatre_halls)

    def test_theatre_hall_str(self):
        self.assertEqual(str(self.theatre_hall), "Theatre Hall")

    def test_theatre_hall_db_name(self):
        self.assertEqual(TheatreHall._meta.db_table, "theatre_hall")


class PlayModelTests(TestCase):
    def setUp(self):
        self.play = create_play()

    def test_create_play(self):
        plays = Play.objects.all()
        self.assertEqual(plays.count(), 1)
        self.assertIn(self.play, plays)

    def test_play_str(self):
        self.assertEqual(str(self.play), "Play")


class PerformanceModelTests(TestCase):
    def setUp(self):
        self.performance = create_performance()

    def test_create_performance(self):
        performances = Performance.objects.all()
        self.assertEqual(performances.count(), 1)
        self.assertIn(self.performance, performances)

    def test_performance_str(self):
        self.assertEqual(
            str(self.performance),
            "Play - 2025-07-28 20:00:00"
        )


class ReservationModelTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.reservation = Reservation.objects.create(user=self.user)

    def test_create_reservation(self):
        reservations = Reservation.objects.all()
        self.assertEqual(reservations.count(), 1)
        self.assertIn(self.reservation, reservations)
        self.assertEqual(self.reservation.user, self.user)

    def test_reservation_str(self):
        self.assertEqual(
            str(self.reservation),
            f"{self.reservation.created_at}"
        )


class TicketModelTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.reservation = Reservation.objects.create(user=self.user)
        self.performance = create_performance()
        self.ticket = Ticket.objects.create(
            row=14,
            seat=10,
            reservation=self.reservation,
            performance=self.performance,
        )

    def test_create_ticket_valid(self):
        tickets = Ticket.objects.all()
        self.assertEqual(tickets.count(), 1)
        self.assertIn(self.ticket, tickets)
        self.assertEqual(self.ticket.row, 14)
        self.assertEqual(self.ticket.seat, 10)

    def test_create_ticket_invalid_row(self):
        with self.assertRaises(ValidationError):
            Ticket.objects.create(
                row=21,
                seat=10,
                reservation=self.reservation,
                performance=self.performance,
            )
        with self.assertRaises(ValidationError):
            Ticket.objects.create(
                row=0,
                seat=10,
                reservation=self.reservation,
                performance=self.performance,
            )

    def test_create_ticket_invalid_seat(self):
        with self.assertRaises(ValidationError):
            Ticket.objects.create(
                row=10,
                seat=21,
                reservation=self.reservation,
                performance=self.performance,
            )
        with self.assertRaises(ValidationError):
            Ticket.objects.create(
                row=10,
                seat=0,
                reservation=self.reservation,
                performance=self.performance,
            )

    def test_ticket_str(self):
        self.assertEqual(
            str(self.ticket),
            f"{str(self.performance)} - (row: 14, seat: 10)"

        )
