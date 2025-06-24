from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path("ws/book-availability/", consumers.BookAvailabilityConsumer.as_asgi()),
]
