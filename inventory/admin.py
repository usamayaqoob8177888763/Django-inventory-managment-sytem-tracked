from django.contrib import admin
from .models import Category, Product

# Category Admin
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)  # description hata diya kyunki model me nahi hai
    search_fields = ('name',)


# Product Admin
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'quantity', 'minimum_stock', 'price')
    list_filter = ('category',)
    search_fields = ('name', 'category__name')
    list_editable = ('quantity', 'minimum_stock', 'price')  # inline edit in list view
    ordering = ('name',)




