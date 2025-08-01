from datetime import datetime
from django.utils.timezone import make_aware
from theatre.models import (
    Genre,
    TheatreHall,
    Play,
    Actor,
    Performance,
    Ticket,
    Reservation
)


def create_genre(**kwargs):
    payload = {
        "name": "Comedy"
    }
    payload.update(**kwargs)
    return Genre.objects.create(**payload)


def create_theatre_hall(**kwargs):
    payload = {
        "name": "Test Hall",
        "rows": 20,
        "seats_in_row": 20
    }
    payload.update(**kwargs)
    return TheatreHall.objects.create(**payload)


def create_actor(**kwargs):
    payload = {
        "first_name": "John",
        "last_name": "Smith",
    }
    payload.update(**kwargs)
    return Actor.objects.create(**payload)


def create_play(**kwargs):
    payload = {
        "title": "Sample Play",
        "description": "Sample description",
    }
    payload.update(**kwargs)
    return Play.objects.create(**payload)


def create_performance(**kwargs):
    theatre_hall = TheatreHall.objects.create(
        name="Test Hall", rows=20, seats_in_row=20
    )
    play = create_play(title="Sample Play", description="Sample description")
    default_show_time = make_aware(datetime(2025, 7, 29, 19, 0, 0))
    payload = {
        "show_time": default_show_time,
        "play": play,
        "theatre_hall": theatre_hall,
    }
    if "show_time" in kwargs and isinstance(kwargs["show_time"], str):
        kwargs["show_time"] = make_aware(
            datetime.fromisoformat(kwargs["show_time"])
        )

    payload.update(**kwargs)
    return Performance.objects.create(**payload)


def create_ticket(reservation: Reservation, **kwargs):
    performance = create_performance()
    payload = {
        "row": 15,
        "seat": 15,
        "performance": performance,
        "reservation": reservation
    }
    payload.update(**kwargs)
    return Ticket.objects.create(**payload)
