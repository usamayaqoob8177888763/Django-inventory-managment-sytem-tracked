from django.urls import path
from . import views

app_name = "billing"

urlpatterns = [
    # customers
    path("customers/", views.customer_list, name="customer_list"),
    path("customers/add/", views.customer_create, name="customer_create"),
    path("customers/<int:pk>/edit/", views.customer_edit, name="customer_edit"),

    # orders
    path("orders/", views.order_list, name="order_list"),
    path("orders/create/", views.order_create, name="order_create"),
    path("orders/<int:pk>/", views.order_detail, name="order_detail"),
    path("orders/<int:pk>/add-payment/", views.add_payment, name="add_payment"),

    # invoice/pdf (optional if WeasyPrint installed)
    path("orders/<int:pk>/invoice/", views.invoice_view, name="invoice_view"),
    path("orders/<int:pk>/invoice.pdf", views.invoice_pdf, name="invoice_pdf"),
]
