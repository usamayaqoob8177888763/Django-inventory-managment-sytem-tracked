from django.shortcuts import render
from django.http import HttpResponse
from .models import Product

# ✅ Home view — must exist for your error to go away
def home(request):
    return HttpResponse("Inventory Home Page")

# ✅ Product list view
def product_list(request):
    products = Product.objects.select_related('category').all()
    return render(request, 'inventory/product_list.html', {'products': products})




