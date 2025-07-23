from django.shortcuts import render
from rest_framework import viewsets, mixins
from theatre.models import (
    TheatreHall,
    Ticket,
    Actor,
    Genre,
    Reservation,
    Play,
    Performance
)
from theatre.serializers import GenreSerializer


class GenreViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


