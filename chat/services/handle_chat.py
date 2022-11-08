import base64
from decouple import config

from chat.models import Message, MessageImage, MessageLike
from django.core.files.base import ContentFile
from users.services import handle_user


def get_message_by_id(message_id):
    return Message.objects.get(pk=message_id)


def get_file_instance_from_base64(base64_string: str):

    formatt, imgstr = base64_string.split(";base64,")
    ext = formatt.split("/")[-1]
    return ContentFile(base64.b64decode(imgstr), name="temp." + ext)


def delete_message_images(message):
    print([image.image.url for image in message.images.all()])
    for image in message.images.all():
        image.delete()


def delete_message(message_id):
    message = Message.objects.get(id=message_id)
    delete_message_images(message)
    message.delete()


def edit(message_id, message_text, images):
    message = Message.objects.get(id=message_id)
    delete_message_images(message)
    for image in images:
        if config("HOST") in image["url"]:
            new_image = MessageImage.objects.create()
            new_image.image.name = image["url"].split("media/")[-1]
            new_image.save()
            message.images.add(new_image)
        else:
            message.images.add(
                MessageImage.objects.get_or_create(
                    image=get_file_instance_from_base64(image["url"])
                )[0]
            )
    message.content = message_text
    message.edited = True
    message.save()

    return message


def get_likes_for_message(message_id):
    return MessageLike.objects.filter(message__id=message_id)


def delete_message_like(message_id, user):
    MessageLike.objects.filter(
        message__id=message_id, user=handle_user.get_user_by_username(user)
    ).delete()


def get_message_parent(parentId):
    if parentId:
        return get_message_by_id(parentId)
