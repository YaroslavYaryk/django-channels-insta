from django.urls import re_path, path
from .views import (
    CustomObtainAuthTokenView,
    CreateUserAPIView,
    LogoutUserAPIView,
    UserAPIView,
    UserDetailsAPIView,
)

urlpatterns = [
    # paths
    path("auth/login/", CustomObtainAuthTokenView.as_view()),
    path("auth/register/", CreateUserAPIView.as_view(), name="auth_user_create"),
    path("auth/logout/", LogoutUserAPIView.as_view(), name="auth_user_logout"),
    # users
    path("all/", UserAPIView.as_view(), name="get_all_users"),
    path("one/", UserDetailsAPIView.as_view(), name="get_one_user"),
    path("one/change/", UserDetailsAPIView.as_view(), name="change_one_user"),
]
