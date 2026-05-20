from django.urls import path

from .consumers import ChatConsumer, ChannelConsumer

websocket_urlpatterns = [
    path('ws/messenger/<int:group_id>/', ChatConsumer.as_asgi()),
    path('ws/channel/<int:channel_id>/', ChannelConsumer.as_asgi()),
]
