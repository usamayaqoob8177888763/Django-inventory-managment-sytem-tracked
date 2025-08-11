from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from .models import Order, OrderItem, Customer, Product
from django.utils import timezone

# 🟢 Order list
def order_list(request):
    orders = Order.objects.select_related('customer').order_by('-date')
    return render(request, 'billing/order_list.html', {'orders': orders})

# 🟢 Order detail
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    return render(request, 'billing/order_detail.html', {'order': order})

# 🟢 Create new order
def order_create(request):
    customers = Customer.objects.all()
    products = Product.objects.all()

    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        customer = get_object_or_404(Customer, id=customer_id)

        tax = float(request.POST.get('tax', 0) or 0)
        discount = float(request.POST.get('discount', 0) or 0)
        payment_status = request.POST.get('payment_status', 'unpaid')

        # ✅ Order create
        order = Order.objects.create(
            customer=customer,
            date=timezone.now(),
            tax=tax,
            discount=discount,
            payment_status=payment_status
        )

        total_amount = 0
        for product in products:
            qty = int(request.POST.get(f'product_{product.id}', 0) or 0)
            if qty > 0:
                subtotal = product.price * qty
                total_amount += subtotal
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    price=product.price,
                    quantity=qty
                )
                # ✅ stock reduce
                product.quantity -= qty
                product.save()

        # ✅ tax and discount apply
        total_amount += tax
        total_amount -= discount
        order.total_amount = total_amount  # make sure field name matches model
        order.save()

        messages.success(request, f"Order #{order.id} created successfully!")
        return redirect('billing:order_detail', pk=order.id)  # ✅ cleaner redirect

    return render(request, 'billing/order_create.html', {
        'customers': customers,
        'products': products
    })

