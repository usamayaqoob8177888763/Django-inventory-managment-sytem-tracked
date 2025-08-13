from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.db import transaction
from django.utils.timezone import now
from django.conf import settings
import os

from inventory.models import Product
from .models import Customer, Order, OrderItem, Payment
from .forms import CustomerForm, PaymentForm

# ---------- Customers ----------
def customer_list(request):
    customers = Customer.objects.order_by("-created_at")
    return render(request, "billing/customer_list.html", {"customers": customers})

def customer_create(request):
    if request.method == "POST":
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Customer added.")
            return redirect("billing:customer_list")
        messages.error(request, "Please fix errors below.")
    else:
        form = CustomerForm()
    return render(request, "billing/customer_form.html", {"form": form, "title": "Add Customer"})

def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == "POST":
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, "Customer updated.")
            return redirect("billing:customer_list")
        messages.error(request, "Please fix errors below.")
    else:
        form = CustomerForm(instance=customer)
    return render(request, "billing/customer_form.html", {"form": form, "title": "Edit Customer"})

# ---------- Orders ----------
def order_list(request):
    orders = Order.objects.select_related("customer").order_by("-date")
    return render(request, "billing/order_list.html", {"orders": orders})

def order_detail(request, pk):
    order = get_object_or_404(Order.objects.select_related("customer"), pk=pk)
    items = order.items.select_related("product").all()
    payments = order.payments.all()
    return render(
        request,
        "billing/order_detail.html",
        {"order": order, "items": items, "payments": payments},
    )

@transaction.atomic
def order_create(request):
    products = Product.objects.all()
    customers = Customer.objects.all()

    if request.method == "POST":
        try:
            customer_id = int(request.POST.get("customer"))
        except (TypeError, ValueError):
            messages.error(request, "Select a customer.")
            return redirect("billing:order_create")

        customer = get_object_or_404(Customer, id=customer_id)
        tax = Decimal(request.POST.get("tax") or 0)
        discount = Decimal(request.POST.get("discount") or 0)
        payment_status = request.POST.get("payment_status") or "unpaid"

        order = Order.objects.create(
            customer=customer,
            created_by=request.user if request.user.is_authenticated else None,
            date=now(),
            tax=tax,
            discount=discount,
            payment_status=payment_status,
        )

        subtotal = Decimal("0.00")
        any_item = False

        for product in products:
            qty_raw = request.POST.get(f"product_{product.id}")
            if not qty_raw:
                continue
            try:
                qty = int(qty_raw)
            except ValueError:
                qty = 0

            if qty > 0:
                any_item = True
                if product.quantity < qty:
                    messages.error(request, f"Not enough stock for {product.name}.")
                    raise transaction.TransactionManagementError("Insufficient stock")

                unit_price = product.price
                line_total = (unit_price * qty).quantize(Decimal("0.01"))
                subtotal += line_total

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    unit_price=unit_price,
                    quantity=qty,
                    line_total=line_total,
                )

                product.quantity -= qty
                product.save(update_fields=["quantity"])

        if not any_item:
            messages.error(request, "Add at least one product quantity.")
            raise transaction.TransactionManagementError("No items")

        order.subtotal = subtotal
        order.total = (subtotal + tax - discount).quantize(Decimal("0.01"))
        order.save()

        messages.success(request, f"Order created: {order.invoice_number}")
        return redirect("billing:order_detail", pk=order.pk)

    return render(request, "billing/order_create.html", {"products": products, "customers": customers})

# ---------- Payments ----------
def add_payment(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.order = order
            payment.save()
            order.refresh_totals()
            order.save(update_fields=["subtotal", "total", "payment_status"])
            messages.success(request, "Payment recorded.")
            return redirect("billing:order_detail", pk=order.pk)
        messages.error(request, "Please fix errors below.")
    else:
        form = PaymentForm()
    return render(request, "billing/payment_form.html", {"form": form, "order": order})

# ---------- Invoice (HTML / PDF) ----------
def invoice_view(request, pk):
    order = get_object_or_404(Order, pk=pk)
    context = {
        "order": order,
        "company_name": "Ittefaq Auto Tractor Spare Parts",
        "company_address": "Main Market, Lahore, Pakistan",
        "company_phone": "+92 300 1234567",
        "company_email": "info@ittefaqtractors.com",
        "logo_url": request.build_absolute_uri("/static/images/tractor_logo.png")
    }
    return render(request, "billing/invoice_template.html", context)

def invoice_pdf(request, pk):
    try:
        from weasyprint import HTML
    except Exception:
        messages.error(request, "WeasyPrint not installed. Install it to generate PDF.")
        return redirect("billing:invoice_view", pk=pk)

    order = get_object_or_404(Order, pk=pk)
    from django.template.loader import render_to_string
    html_string = render_to_string(
        "billing/invoice_template.html",
        {
            "order": order,
            "company_name": "Ittefaq Auto Tractor Spare Parts",
            "company_address": "Main Market, Lahore, Pakistan",
            "company_phone": "+92 300 1234567",
            "company_email": "info@ittefaqtractors.com",
            "logo_url": request.build_absolute_uri("/static/images/tractor_logo.png")
        }
    )

    base_url = str(settings.BASE_DIR)  # FIX for WindowsPath
    pdf = HTML(string=html_string, base_url=base_url).write_pdf()

    from django.http import HttpResponse
    filename = f"invoice_{order.invoice_number}.pdf"
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{filename}"'
    return response
