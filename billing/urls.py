# billing/urls.py
from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    path('orders/create/', views.order_create, name='order_create'),  # ✅ match views.py
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),
    path('orders/', views.order_list, name='order_list'),
]
