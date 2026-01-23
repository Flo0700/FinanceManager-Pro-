from django.urls import path

from . import views

app_name = "authentication"

urlpatterns = [
    path("register", views.auth_register, name="register"),
    path("login", views.auth_login, name="login"),
    path("google", views.auth_google, name="google"),
    path("refresh", views.auth_refresh, name="refresh"),
    path("logout", views.auth_logout, name="logout"),
    path(
        "verify-email-status",
        views.auth_verify_email_status,
        name="verify-email-status",
    ),
    path(
        "resend-verification",
        views.auth_resend_verification,
        name="resend-verification",
    ),
]
