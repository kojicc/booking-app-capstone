from django.urls import path, include
from .views import UserList, UserDetail, RegisterUser, LoginUser, RefreshTokenView, LogoutView, CurrentUserView

urlpatterns = [
    # Authentication endpoints
    path("register/", RegisterUser.as_view(), name="user-register"),
    path("login/", LoginUser.as_view(), name="user-login"),
    path("refresh/", RefreshTokenView.as_view(), name="token-refresh"),
    path("logout/", LogoutView.as_view(), name="user-logout"),
    path("me/", CurrentUserView.as_view(), name="current-user"),

    # User CRUD endpoints
    path("", UserList.as_view(), name="user-list"),
    path("<int:pk>/", UserDetail.as_view(), name="user-detail"),
]
