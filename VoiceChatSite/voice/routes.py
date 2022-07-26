from django.urls import re_path, path

from . import consumers

websocket_urlpatterns = [
    path('voice/ws/player/data/', consumers.PlayerDataConsumer.as_asgi()),
    path('voice/ws/server/', consumers.ServerConsumer.as_asgi()),
    path('voice/ws/player/voice/', consumers.PlayerVoiceConsumer.as_asgi())
]