from django.db import IntegrityError
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response

from django.contrib.auth import get_user_model
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework import status
from rest_framework.views import APIView
from .serializers import CreateUserSerializer, UserSerializer


class CustomObtainAuthTokenView(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, created = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "username": user.username})


class CreateUserAPIView(CreateAPIView):
    serializer_class = CreateUserSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=False)
        try:
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            # We create a token than will be used for future auth
            token = Token.objects.create(user=serializer.instance)
            token_data = {"token": token.key}
            return Response(
                {**serializer.data, **token_data},
                status=status.HTTP_201_CREATED,
                headers=headers,
            )
        except IntegrityError as err:
            return Response({"message": str(err)}, status.HTTP_401_UNAUTHORIZED)


class LogoutUserAPIView(APIView):
    queryset = get_user_model().objects.all()

    def get(self, request, format=None):
        # simply delete the token to force a login
        request.user.auth_token.delete()
        return Response(status=status.HTTP_200_OK)


class UserAPIView(APIView):
    def get_queryset(self):
        queryset = get_user_model().objects.all()
        return queryset

    def get(self, request, format=None):
        # simply delete the token to force a login
        queryset = self.get_queryset()
        serializer = UserSerializer(queryset, many=True)
        return Response(serializer.data)
