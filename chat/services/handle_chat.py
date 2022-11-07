import base64
from decouple import config

from chat.models import Message, MessageImage
from django.core.files.base import ContentFile


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
    message.save()

    return message
