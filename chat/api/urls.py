from django.urls import path
from .views import (
    ConversationAPIView,
    MessageAPIView,
    ConversationBaseAPIView,
    MessageListAPIView,
    MessageSingleAPIView,
)

urlpatterns = [
    path(
        "active_conversation/",
        ConversationAPIView.as_view(),
        name="get_active_conversation",
    ),
    path(
        "conversation/<conversation_name>/",
        ConversationBaseAPIView.as_view(),
        name="get_conversation_by_name",
    ),
    path("messages/", MessageAPIView.as_view(), name="get_messages_for_conversation"),
    path("all_messages/", MessageListAPIView.as_view(), name="get_all_messages"),
    path(
        "messages/<conversation_name>/<message_id>/",
        MessageSingleAPIView.as_view(),
        name="get_single_message",
    ),
]
