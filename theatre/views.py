from django.db.models import F, Count
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from theatre.models import (
    TheatreHall,
    Actor,
    Genre,
    Reservation,
    Play,
    Performance
)
from theatre.permissions import IsAdminOrIfAuthenticatedReadOnly
from theatre.serializers import (
    GenreSerializer,
    ActorSerializer,
    TheatreHallSerializer,
    PlaySerializer,
    PlayListSerializer,
    PlayRetrieveSerializer,
    PerformanceSerializer,
    PerformanceListSerializer,
    PerformanceRetrieveSerializer,
    ReservationSerializer,
    ReservationListSerializer, PlayImageSerializer
)


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

        elif self.action == "upload_image":
            return PlayImageSerializer

        return PlaySerializer

    def get_queryset(self):
        queryset = self.queryset
        if self.action in ("list", "retrieve"):
            queryset = queryset.prefetch_related("actors", "genres")

        return queryset

    @action(
        methods=["POST"],
        detail=True,
        url_path="upload-image"
    )
    def upload_image(self, request, pk=None):
        play = self.get_object()
        serializer = self.get_serializer(play, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
    permission_classes = (IsAuthenticated, )

    def get_queryset(self):
        queryset = self.queryset
        return queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return ReservationListSerializer

        return ReservationSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
