from django.db.models import F, Count
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
    PlayListSerializer, PlayRetrieveSerializer, PerformanceSerializer, PerformanceListSerializer, \
    PerformanceRetrieveSerializer, ReservationSerializer, ReservationListSerializer


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


class PerformanceViewSet(
    viewsets.ModelViewSet
):
    queryset = (
        Performance.objects.all()
        .select_related("play", "theatre_hall")
        .annotate(
            tickets_available=(
                F("theatre_hall__rows") * F("theatre_hall__seats_in_row")
                - Count("tickets")
            )
        )
    )
    serializer_class = PerformanceSerializer

    def get_queryset(self):
        queryset = self.queryset
        if self.action in ("list", "retrieve"):
            queryset = queryset.select_related("play", "theatre_hall")
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return PerformanceListSerializer

        elif self.action == "retrieve":
            return PerformanceRetrieveSerializer

        return PerformanceSerializer


class ReservationViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Reservation.objects.prefetch_related(
        "tickets__performance__play", "tickets__performance__theatre_hall"
    )
    serializer_class = ReservationSerializer

    def get_queryset(self):
        queryset = self.queryset
        return Reservation.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return ReservationListSerializer

        return ReservationSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
