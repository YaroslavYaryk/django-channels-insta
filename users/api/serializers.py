from django.contrib.auth import get_user_model
from rest_framework import serializers
from decouple import config


class CreateUserSerializer(serializers.ModelSerializer):
    email = serializers.CharField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model = get_user_model()
        fields = (
            "email",
            "password",
            "username",
        )
        write_only_fields = "password"
        read_only_fields = (
            "is_staff",
            "is_superuser",
            "is_active",
        )

    def create(self, validated_data):
        user = super(CreateUserSerializer, self).create(validated_data)
        user.set_password(validated_data["password"])
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):

    image = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = ("id", "username", "email", "first_name", "last_name", "image")

    def get_image(self, instance):
        try:
            return f"{config('HOST')}:{config('PORT')}{instance.image.url}"
        except:
            return None
