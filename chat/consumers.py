from channels.generic.websocket import JsonWebsocketConsumer
from django.contrib.auth import get_user_model
from asgiref.sync import async_to_sync
from .models import Conversation, Message, MessageImage, MessageLike
from chat.api.serializers import MessageSerializer, MessageLikeSerializer
import json
from uuid import UUID
from datetime import datetime
from users.api.serializers import UserSerializer
from .services import handle_chat
from users.services import handle_user
from decouple import config

User = get_user_model()


class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            # if the obj is uuid, we simply return the value of uuid
            return obj.hex
        return json.JSONEncoder.default(self, obj)


class ChatConsumer(JsonWebsocketConsumer):
    """
    This consumer is used to show user's online status,
    and send notifications.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.user = None
        self.conversation_name = None
        self.conversation = None

    def connect(self):

        self.user = self.scope["user"]
        if not self.user.is_authenticated:  # check if authenticated
            return

        self.accept()

        self.conversation_name = (
            f"{self.scope['url_route']['kwargs']['conversation_name']}"
        )
        participants = self.conversation_name.split("__")
        print(participants)
        if participants[0] != participants[1]:
            self.conversation, created = Conversation.objects.get_or_create(
                name=self.conversation_name
            )

        async_to_sync(self.channel_layer.group_add)(
            self.conversation_name,
            self.channel_name,
        )

        self.send_json(
            {
                "type": "online_user_list",
                "users": [user.username for user in self.conversation.online.all()],
            }
        )

        # async_to_sync(self.channel_layer.group_send)(
        #     self.conversation_name,
        #     {
        #         "type": "user_join",
        #         "user": self.user.username,
        #     },
        # )

        # self.conversation.online.add(self.user)

        messages = self.conversation.messages.all().order_by("-timestamp")[0:30]
        message_count = self.conversation.messages.all().count()
        self.send_json(
            {
                "type": "last_30_messages",
                "messages": MessageSerializer(messages, many=True).data,
                "has_more": message_count > 30,
            }
        )

    def disconnect(self, code):

        # if self.user.is_authenticated:  # send the leave event to the room
        #     async_to_sync(self.channel_layer.group_send)(
        #         self.conversation_name,
        #         {
        #             "type": "user_leave",
        #             "user": self.user.username,
        #         },
        #     )
        #     self.conversation.online.remove(self.user)

        return super().disconnect(code)

    def chat_message_echo(self, event):
        self.send_json(event)

    def get_receiver(self):
        usernames = self.conversation_name.split("__")
        for username in usernames:
            if username != self.user.username:
                # This is the receiver
                return User.objects.get(username=username)

    def receive_json(self, content, **kwargs):
        message_type = content["type"]

        if message_type == "typing":
            async_to_sync(self.channel_layer.group_send)(
                self.conversation_name,
                {
                    "type": "typing",
                    "user": self.user.username,
                    "typing": content["typing"],
                },
            )

        if message_type == "chat_message":
            print("chat_message")

            conversation = (
                handle_chat.get_conversation_by_name(content["conversation_name"])
                or self.conversation
            )

            message = Message.objects.create(
                from_user=self.user,
                to_user=self.get_receiver(),
                content=content["message"],
                conversation=conversation,
                parent=handle_chat.get_message_parent(content.get("parent")),
                forwarded=content["forwarded"],
            )
            if content["filesBase64"]:
                for elem in content["filesBase64"]:

                    if config("HOST") in elem["url"]:
                        new_image = MessageImage.objects.create()
                        new_image.image.name = elem["url"].split("media/")[-1]
                        new_image.save()
                        message.images.add(new_image)
                    else:
                        message.images.add(
                            MessageImage.objects.get_or_create(
                                image=handle_chat.get_file_instance_from_base64(
                                    elem["url"]
                                )
                            )[0]
                        )
                message.save()

            async_to_sync(self.channel_layer.group_send)(
                conversation.name,
                {
                    "type": "chat_message_echo",
                    "name": self.user.username,
                    "message": MessageSerializer(message).data,
                },
            )

            async_to_sync(self.channel_layer.group_send)(
                "conversations",
                {
                    "type": "new_unread_message",
                    "name": conversation.name,
                    "from_user": self.user.username,
                    "message": MessageSerializer(message).data,
                },
            )

            notification_group_name = self.get_receiver().username + "__notifications"
            async_to_sync(self.channel_layer.group_send)(
                notification_group_name,
                {
                    "type": "new_message_notification",
                    "name": self.user.username,
                    "message": MessageSerializer(message).data,
                },
            )

        if message_type == "read_messages":
            messages_to_me = self.conversation.messages.filter(
                to_user=self.user
            ).order_by("-timestamp")

            messages_to_me.update(read=True)

            # messages = self.conversation.messages.all().order_by("-timestamp")[0:30]
            # message_count = self.conversation.messages.all().count()
            async_to_sync(self.channel_layer.group_send)(
                self.conversation_name,
                {"type": "read_messages", "user": self.user.username},
            )

            # Update the unread message count
            unread_count = Message.objects.filter(to_user=self.user, read=False).count()
            async_to_sync(self.channel_layer.group_send)(
                self.user.username + "__notifications",
                {
                    "type": "unread_count",
                    "unread_count": unread_count,
                },
            )

            unread_messages = json.dumps(
                [
                    {
                        "name": conv.name,
                        "count": conv.messages.filter(
                            to_user=self.user, read=False
                        ).count(),
                    }
                    for conv in Conversation.objects.filter(
                        name__contains=self.user.username
                    )
                ]
            )
            try:
                message = self.conversation.messages.all().order_by("-timestamp")[0]
                async_to_sync(self.channel_layer.group_send)(
                    "conversations",
                    {
                        "type": "unread_messages",
                        "unread_messages": unread_messages,
                        "user": self.user.username,
                        "name": self.conversation.name,
                        "message": MessageSerializer(message).data,
                    },
                )
            except:
                pass

        if message_type == "delete_message":

            message_id = content["messageId"]
            handle_chat.delete_message(message_id)

            async_to_sync(self.channel_layer.group_send)(
                self.conversation_name,
                {"type": "delete_message", "message_id": message_id},
            )

            try:
                message = self.conversation.messages.all().order_by("-timestamp")[0]
                async_to_sync(self.channel_layer.group_send)(
                    "conversations",
                    {
                        "type": "change_last_message",
                        "name": self.conversation.name,
                        "message": MessageSerializer(message).data,
                    },
                )

            except:
                pass
            async_to_sync(self.channel_layer.group_send)(
                "conversations",
                {
                    "type": "delete_last_unread",
                    "name": self.conversation.name,
                    "from_user": self.user.username,
                    "message": MessageSerializer(message).data,
                },
            )

        if message_type == "edit_message":
            message_id = content["messageId"]
            message = handle_chat.edit(
                message_id, content["message"], content["filesBase64"]
            )

            async_to_sync(self.channel_layer.group_send)(
                self.conversation_name,
                {"type": "edit_message", "message": MessageSerializer(message).data},
            )

            try:
                async_to_sync(self.channel_layer.group_send)(
                    "conversations",
                    {
                        "type": "change_last_message",
                        "name": self.conversation.name,
                        "message": MessageSerializer(message).data,
                    },
                )
            except:
                pass

        if message_type == "create_message_like":
            message_like = MessageLike.objects.get_or_create(
                message=handle_chat.get_message_by_id(content["messageId"]),
                user=handle_user.get_user_by_username(content["user"]),
            )[0]
            async_to_sync(self.channel_layer.group_send)(
                self.conversation_name,
                {
                    "type": "message_like",
                    "message_likes": MessageLikeSerializer(
                        handle_chat.get_likes_for_message(content["messageId"]),
                        many=True,
                    ).data,
                    "message_id": content["messageId"],
                },
            )

        if message_type == "delete_message_like":
            handle_chat.delete_message_like(content["messageId"], self.user)
            async_to_sync(self.channel_layer.group_send)(
                self.conversation_name,
                {
                    "type": "message_like",
                    "message_likes": MessageLikeSerializer(
                        handle_chat.get_likes_for_message(content["messageId"]),
                        many=True,
                    ).data,
                    "message_id": content["messageId"],
                },
            )

        return super().receive_json(content, **kwargs)

    def user_join(self, event):
        self.send_json(event)

    def user_leave(self, event):
        self.send_json(event)

    def typing(self, event):
        self.send_json(event)

    def new_message_notification(self, event):
        self.send_json(event)

    def last_30_messages(self, event):
        self.send_json(event)

    def unread_count(self, event):
        self.send_json(event)

    def new_unread_message(self, event):
        self.send_json(event)

    def unread_messages(self, event):
        self.send_json(event)

    def read_messages(self, event):
        self.send_json(event)

    def change_last_message(self, event):
        self.send_json(event)

    def delete_message(self, event):
        self.send_json(event)

    def delete_last_unread(self, event):
        self.send_json(event)

    def edit_message(self, event):
        self.send_json(event)

    def message_like(self, event):
        self.send_json(event)

    @classmethod
    def encode_json(cls, content):
        return json.dumps(content, cls=UUIDEncoder)


class ConversationConsumer(JsonWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.user = None
        self.message_group_name = None

    def connect(self):

        self.user = self.scope["user"]
        if not self.user.is_authenticated:  # check if authenticated
            return

        self.accept()

        print("connect")

        self.message_group_name = self.user.username + "__conversations"
        async_to_sync(self.channel_layer.group_add)(
            "conversations",
            self.channel_name,
        )

        self.send_json(
            {
                "type": "online_user_list",
                "users": [
                    user.username
                    for conversation in Conversation.objects.filter(
                        name__contains=self.user.username
                    )
                    for user in conversation.online.all()
                ],
            }
        )

        async_to_sync(self.channel_layer.group_send)(
            "conversations",
            {
                "type": "user_join",
                "user": self.user.username,
            },
        )

        for group in Conversation.objects.filter(name__contains=self.user.username):
            async_to_sync(self.channel_layer.group_send)(
                group.name,
                {
                    "type": "user_join",
                    "user": self.user.username,
                },
            )

        for conversation in Conversation.objects.filter(
            name__contains=self.user.username
        ):
            if not conversation.online.filter(id=self.user.id):
                conversation.online.add(self.user)

        # Send count of unread messages
        unread_messages = json.dumps(
            [
                {
                    "name": conv.name,
                    "count": conv.messages.filter(
                        to_user=self.user, read=False
                    ).count(),
                }
                for conv in Conversation.objects.filter(
                    name__contains=self.user.username
                )
            ]
        )
        self.send_json(
            {
                "type": "unread_messages",
                "unread_messages": unread_messages,
                "user": self.user.username,
            }
        )

    def disconnect(self, code):
        if self.user.is_authenticated:  # send the leave event to the room

            self.user.last_login = datetime.now()
            self.user.save()

            async_to_sync(self.channel_layer.group_send)(
                "conversations",
                {
                    "type": "user_leave",
                    "user": self.user.username,
                    "updated_user": UserSerializer(self.user).data,
                },
            )

            for group in Conversation.objects.filter(name__contains=self.user.username):
                async_to_sync(self.channel_layer.group_send)(
                    group.name,
                    {
                        "type": "user_leave",
                        "user": self.user.username,
                    },
                )

        print("disconnect")
        for conversation in Conversation.objects.filter(
            name__contains=self.user.username
        ):
            conversation.online.remove(self.user)

        return super().disconnect(code)

    def receive_json(self, content, **kwargs):
        message_type = content["type"]

        return super().receive_json(content, **kwargs)

    def user_join(self, event):
        self.send_json(event)

    def user_leave(self, event):
        self.send_json(event)

    def new_unread_message(self, event):
        self.send_json(event)

    def unread_messages(self, event):
        self.send_json(event)

    def change_last_message(self, event):
        self.send_json(event)

    def delete_last_unread(self, event):
        self.send_json(event)


class NotificationConsumer(JsonWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.notification_group_name = None
        self.user = None

    def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            return

        self.accept()

        # private notification group
        self.notification_group_name = self.user.username + "__notifications"
        async_to_sync(self.channel_layer.group_add)(
            self.notification_group_name,
            self.channel_name,
        )

        # Send count of unread messages
        unread_count = Message.objects.filter(to_user=self.user, read=False).count()
        self.send_json(
            {
                "type": "unread_count",
                "unread_count": unread_count,
            }
        )

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            self.notification_group_name,
            self.channel_name,
        )
        return super().disconnect(code)

    def new_message_notification(self, event):
        self.send_json(event)

    def unread_count(self, event):
        self.send_json(event)
