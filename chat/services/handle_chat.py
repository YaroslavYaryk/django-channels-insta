import base64

from django.core.files.base import ContentFile


def get_file_instance_from_base64(base64_string: str):

    formatt, imgstr = base64_string.split(";base64,")
    ext = formatt.split("/")[-1]
    return ContentFile(base64.b64decode(imgstr), name="temp." + ext)
