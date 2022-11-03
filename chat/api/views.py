from rest_framework.response import Response

from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from chat.models import Conversation

from chat.models import Message
from .paginaters import MessagePagination
from .serializers import (
    MessageSerializer,
    ConversationBaseSerializer,
    ConversationSerializer,
)


class ConversationAPIView(APIView):
    def get_queryset(self):
        queryset = Conversation.objects.filter(
            name__contains=self.request.user.username
        )
        return queryset

    def get(self, request, format=None):
        # simply delete the token to force a login
        queryset = self.get_queryset()
        serializer = ConversationSerializer(queryset, many=True, user=self.request.user)
        return Response(serializer.data)


class ConversationBaseAPIView(APIView):
    def get(self, request, conversation_name):
        # simply delete the token to force a login
        queryset = Conversation.objects.filter(name=conversation_name)
        serializer = ConversationSerializer(queryset, many=True, user=self.request.user)
        try:
            return Response(serializer.data[0])
        except Exception:
            return Response({})


class MessageAPIView(ListAPIView):
    pagination_class = MessagePagination
    serializer_class = MessageSerializer

    def get_queryset(self):
        conversation_name = self.request.GET.get("conversation")
        queryset = (
            Message.objects.filter(
                conversation__name__contains=self.request.user.username,
            )
            .filter(conversation__name=conversation_name)
            .order_by("-timestamp")
        )
        return queryset

    # def get(self, request):
    #     queryset = self.get_queryset()
    #     serializer = MessageSerializer(queryset, many=True)
    #     return Response(serializer.data)