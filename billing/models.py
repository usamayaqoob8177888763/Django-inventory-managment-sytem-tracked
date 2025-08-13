from django.db import models
from django.conf import settings
from decimal import Decimal
from django.utils import timezone
from inventory.models import Product  # <- use existing inventory Product


class Customer(models.Model):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class Order(models.Model):
    PAYMENT_STATUS = [
        ("unpaid", "Unpaid"),
        ("partial", "Partial"),
        ("paid", "Paid"),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="orders")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateTimeField(default=timezone.now)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    invoice_number = models.CharField(max_length=50, unique=True, blank=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default="unpaid")
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return self.invoice_number or f"Order #{self.pk}"

    @property
    def amount_paid(self):
        return self.payments.aggregate(x=models.Sum("amount"))["x"] or Decimal("0.00")

    @property
    def balance(self):
        return (self.total or Decimal("0.00")) - self.amount_paid

    def refresh_totals(self):
        items_total = self.items.aggregate(x=models.Sum("line_total"))["x"] or Decimal("0.00")
        self.subtotal = items_total
        self.total = (items_total + (self.tax or 0) - (self.discount or 0)).quantize(Decimal("0.01"))
        # payment status
        paid = self.amount_paid
        if paid <= 0:
            self.payment_status = "unpaid"
        elif paid < self.total:
            self.payment_status = "partial"
        else:
            self.payment_status = "paid"

    def save(self, *args, **kwargs):
        creating = self.pk is None
        super().save(*args, **kwargs)
        if creating and not self.invoice_number:
            self.invoice_number = f"INV-{self.date.strftime('%Y%m%d')}-{self.id:05d}"
            super().save(update_fields=["invoice_number"])


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField()
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.product.name} × {self.quantity}"

    def save(self, *args, **kwargs):
        self.unit_price = self.unit_price or self.product.price
        self.line_total = (self.unit_price * self.quantity).quantize(Decimal("0.01"))
        super().save(*args, **kwargs)


class Payment(models.Model):
    METHOD_CHOICES = [
        ("cash", "Cash"),
        ("card", "Card"),
        ("bank", "Bank Transfer"),
        ("online", "Online"),
    ]
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default="cash")
    reference = models.CharField(max_length=100, blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"Payment {self.amount} for {self.order.invoice_number}"
