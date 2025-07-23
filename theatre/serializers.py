from rest_framework import serializers
from theatre.models import (
    Ticket,
    TheatreHall,
    Actor,
    Genre,
    Reservation,
    Play,
    Performance
)


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ("id", "name")
