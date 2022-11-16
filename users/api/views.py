from django.db import IntegrityError
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response

from django.contrib.auth import get_user_model
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework import status
from rest_framework.views import APIView
from .serializers import CreateUserSerializer, UserPutSerializer, UserSerializer

from users.services import handle_user


class CustomObtainAuthTokenView(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        message = ""
        serializer = ""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            user = serializer.validated_data["user"]
            token, created = Token.objects.get_or_create(user=user)
            return Response({"token": token.key, "username": user.username})

        except Exception as err:
            message = "\n".join(
                [el.title() for values in serializer.errors.values() for el in values]
            )
            print(err)
            return Response({"message": message}, status.HTTP_401_UNAUTHORIZED)


class CreateUserAPIView(CreateAPIView):
    serializer_class = CreateUserSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=False)
        message = "\n".join(
            [el.title() for values in serializer.errors.values() for el in values]
        )
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
        except Exception as err:
            return Response(
                {"message": message or str(err)}, status.HTTP_401_UNAUTHORIZED
            )


class LogoutUserAPIView(APIView):
    queryset = get_user_model().objects.all()

    def get(self, request, format=None):
        # simply delete the token to force a login
        request.user.auth_token.delete()
        return Response(status=status.HTTP_200_OK)


class UserAPIView(APIView):
    def get_queryset(self):
        queryset = get_user_model().objects.all().exclude(id=self.request.user.id)
        return queryset

    def get(self, request, format=None):
        # simply delete the token to force a login
        queryset = self.get_queryset()
        serializer = UserSerializer(queryset, many=True)
        return Response(serializer.data)


class UserDetailsAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        print(self.request.user)
        queryset = self.request.user
        return queryset

    def get(self, request, format=None):
        # simply delete the token to force a login
        queryset = self.get_queryset()
        serializer = UserSerializer(queryset)
        return Response(serializer.data)

    def put(self, request):

        data = {
            "first_name": request.data["first_name"],
            "last_name": request.data["last_name"],
            "username": request.data["username"],
            "email": request.data["email"],
        }

        serializer = UserPutSerializer(data=data, instance=request.user)
        if serializer.is_valid():
            instance = serializer.save(comit=False)
            if not request.data.get("old"):
                instance.image = request.data["image"]
                print("chnage", request.data["image"])
            instance.save()
            new_serializer = UserSerializer(instance)
            return Response(new_serializer.data)

        message = "\n".join(
            [el.title() for values in serializer.errors.values() for el in values]
        )
        return Response({"message": message}, status=status.HTTP_400_BAD_REQUEST)
