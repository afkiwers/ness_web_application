from django.urls import re_path
from ness_comms.consumers import PanelStatusConsumer, AlarmHistoryConsumer

websocket_urlpatterns = [
    re_path(r'^ws/panel/$', PanelStatusConsumer.as_asgi()),
    re_path(r'^ws/history/$', AlarmHistoryConsumer.as_asgi()),
]
