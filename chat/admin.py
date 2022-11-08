from django.contrib import admin

# Register your models here.
from .models import Conversation, Message, MessageImage, MessageLike


admin.site.register(Conversation)
admin.site.register(Message)
admin.site.register(MessageImage)
admin.site.register(MessageLike)
