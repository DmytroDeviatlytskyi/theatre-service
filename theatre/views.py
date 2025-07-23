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
from theatre.serializers import GenreSerializer, ActorSerializer, TheatreHallSerializer, PlaySerializer, \
    PlayListSerializer, PlayRetrieveSerializer


class GenreViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class ActorViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer


class TheatreHallViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = TheatreHall.objects.all()
    serializer_class = TheatreHallSerializer


class PlayViewSet(
    viewsets.ModelViewSet
):
    queryset = Play.objects.all()
    serializer_class = PlaySerializer


    def get_serializer_class(self):
        if self.action == "list":
            return PlayListSerializer

        elif self.action == "retrieve":
            return PlayRetrieveSerializer
        return PlaySerializer


    def get_queryset(self):
        queryset = self.queryset
        if self.action in ("list", "retrieve"):
            queryset = queryset.prefetch_related("actors", "genres")

        return queryset
