from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    image = models.ImageField(upload_to="profile_photos/", null=True)
    last_login = models.DateTimeField(null=True)


# you can add more fields here.
