from django.urls import path, include
from rest_framework import routers

from theatre.views import GenreViewSet


app_name = "theatre"

router = routers.DefaultRouter()
router.register("genres", GenreViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
