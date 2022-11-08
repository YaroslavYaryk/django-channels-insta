from rest_framework import serializers
from decouple import config
from chat.models import Message, Conversation, MessageLike
from users.api.serializers import UserSerializer

from django.contrib.auth import get_user_model

User = get_user_model()


class MessageLikeSerializer(serializers.ModelSerializer):

    user = serializers.SerializerMethodField()
    message = serializers.SerializerMethodField()

    class Meta:
        model = MessageLike
        fields = "message", "user"

    def get_message(self, instance):
        return str(instance.message.id)

    def get_user(self, instance):
        return instance.user.username


class MessageSerializer(serializers.ModelSerializer):
    from_user = UserSerializer()
    to_user = UserSerializer()
    conversation = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    likes = serializers.SerializerMethodField()
    parent = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = (
            "id",
            "conversation",
            "from_user",
            "to_user",
            "images",
            "content",
            "timestamp",
            "read",
            "edited",
            "likes",
            "parent",
        )

    def get_conversation(self, obj):
        return str(obj.conversation.id)

    def get_images(self, instance):
        try:
            return [
                f"{config('HOST')}:{config('PORT')}{img.image.url}"
                for img in instance.images.all()
            ]
        except:
            return None

    def get_parent(self, instance):
        if instance.parent:
            return str(instance.parent.id)

    def get_likes(self, instance):
        queryset = MessageLike.objects.filter(message=instance)
        # serializer = MessageLikeSerializer(queryset, many=True)
        # if serializer.is_valid():
        return MessageLikeSerializer(queryset, many=True).data
        print(serializer.errors)

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
