# accounts/urls.py


from django.urls import path
from . import views

urlpatterns = [
    # API endpoints
    path("api/auth/register/user/",
         views.UserRegisterAPIView.as_view(),
         name="api_user_register"),
    path("api/auth/register/driver/",
         views.DriverRegisterAPIView.as_view(),
         name="api_driver_register"),
    path("api/auth/login/",
         views.LoginAPIView.as_view(),
         name="api_login"),
    path("api/auth/logout/",
         views.LogoutAPIView.as_view(),
         name="api_logout"),
    path("api/auth/profile/",
         views.ProfileAPIView.as_view(),
         name="api_profile"),
    path("api/auth/forgot-password/",
         views.ForgotPasswordAPIView.as_view(),
         name="api_forgot_password"),

    # HTML page routes

    path("accounts/login/", views.login_page,
         name="login_page"),
    path("accounts/logout/", views.logout_view,
         name="logout"),
    path("accounts/register/user/",
         views.user_register_page,
         name="user_register_page"),
    path("accounts/register/driver/",
         views.driver_register_page,
         name="driver_register_page"),
    path("accounts/forgot-password/",
         views.forgot_password_page,
         name="forgot_password_page"),
]
