from django.urls import re_path, path
from .views import (
    CustomObtainAuthTokenView,
    CreateUserAPIView,
    LogoutUserAPIView,
    UserAPIView,
)

urlpatterns = [
    # paths
    path("auth/login/", CustomObtainAuthTokenView.as_view()),
    path("auth/register/", CreateUserAPIView.as_view(), name="auth_user_create"),
    path("auth/logout/", LogoutUserAPIView.as_view(), name="auth_user_logout"),
    # users
    path("all/", UserAPIView.as_view(), name="get_all_users"),
]
