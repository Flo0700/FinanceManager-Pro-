from django.urls import path

from . import views

app_name = "companies"

urlpatterns = [
    path("", views.company_list, name="list"),
    path("create", views.company_create, name="create"),
    path("<uuid:company_id>", views.company_detail, name="detail"),
]
