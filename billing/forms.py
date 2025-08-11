from django import forms
from .models import Customer, Order

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'phone', 'email', 'address']


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['customer', 'tax', 'discount', 'payment_status']
