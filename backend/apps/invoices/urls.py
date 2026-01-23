from django.urls import path

from . import views

app_name = "invoices"

urlpatterns = [
    # Invoices
    path("", views.invoice_list, name="list"),
    path("create", views.invoice_create, name="create"),
    path("<uuid:invoice_id>", views.invoice_detail, name="detail"),
    path("<uuid:invoice_id>/validate", views.invoice_validate, name="validate"),
    path("<uuid:invoice_id>/cancel", views.invoice_cancel, name="cancel"),
    # Customers
    path("customers/", views.customer_list, name="customer_list"),
    path("customers/create", views.customer_create, name="customer_create"),
    path("customers/<uuid:customer_id>", views.customer_detail, name="customer_detail"),
    path(
        "customers/<uuid:customer_id>/update",
        views.customer_update,
        name="customer_update",
    ),
    path(
        "customers/<uuid:customer_id>/delete",
        views.customer_delete,
        name="customer_delete",
    ),
]
