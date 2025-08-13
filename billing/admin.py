from django.contrib import admin
from .models import Customer, Order, OrderItem, Payment

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "email", "created_at")
    search_fields = ("name", "phone", "email")

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("line_total",)

class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("invoice_number", "customer", "date", "subtotal", "tax", "discount", "total", "payment_status")
    search_fields = ("invoice_number", "customer__name")
    list_filter = ("payment_status", "date")
    inlines = [OrderItemInline, PaymentInline]
    readonly_fields = ("invoice_number", "subtotal", "total")

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("order", "amount", "method", "date", "reference")
    search_fields = ("order__invoice_number", "reference")
