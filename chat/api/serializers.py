from rest_framework import serializers

from chat.models import Message, Conversation
from users.api.serializers import UserSerializer

from django.contrib.auth import get_user_model

User = get_user_model()


class MessageSerializer(serializers.ModelSerializer):
    from_user = UserSerializer()
    to_user = UserSerializer()
    conversation = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = (
            "id",
            "conversation",
            "from_user",
            "to_user",
            "content",
            "timestamp",
            "read",
        )

    def get_conversation(self, obj):
        return str(obj.conversation.id)

    # def get_from_user(self, obj):
    #     return UserSerializer(obj.from_user).data

    # def get_to_user(self, obj):
    #     return UserSerializer(obj.to_user).data


class ConversationSerializer(serializers.ModelSerializer):
    other_user = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ("id", "name", "other_user", "last_message")

    def __init__(self, instance=None, data=..., user=0, *args, **kwargs):
        self.user = user
        super().__init__(instance, data, *args, **kwargs)

    def get_last_message(self, obj):
        messages = obj.messages.all().order_by("-timestamp")
        if not messages.exists():
            return None
        message = messages[0]
        return MessageSerializer(message).data

    def get_other_user(self, obj, *args, **kwargs):
        usernames = obj.name.split("__")
        for username in usernames:
            if username != self.user.username:
                # This is the other participant
                other_user = User.objects.get(username=username)
                return UserSerializer(other_user).data


class ConversationBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = "__all__"
