from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from store.models import Product, ProductVariant
from .models import Order, OrderItem


def get_cart_items(request):
    """
    Retrieve all items from the session cart.
    Returns a list of dicts with product, variant, quantity, price, total, and session key.
    Also cleans up any items whose product or variant no longer exist.
    """
    cart = request.session.get('cart', {})
    items = []
    product_ids = []
    variant_ids = []

    # Collect IDs for bulk queries
    for key, data in cart.items():
        product_ids.append(data['product_id'])
        if data.get('variant_id'):
            variant_ids.append(int(data['variant_id']))

    # Fetch products and variants
    products = Product.objects.filter(id__in=product_ids)
    variants = ProductVariant.objects.filter(id__in=variant_ids) if variant_ids else []

    product_dict = {p.id: p for p in products}
    variant_dict = {v.id: v for v in variants}

    # Build items and detect invalid entries
    to_delete = []
    for key, data in cart.items():
        product = product_dict.get(data['product_id'])
        if not product:
            to_delete.append(key)
            continue

        variant = None
        if data.get('variant_id'):
            try:
                vid = int(data['variant_id'])
                variant = variant_dict.get(vid)
            except (ValueError, TypeError):
                variant = None
            if not variant:
                to_delete.append(key)
                continue

        price = variant.price if variant and variant.price else product.price
        subtotal = price * data['quantity']
        items.append({
            'product': product,
            'variant': variant,
            'quantity': data['quantity'],
            'price': price,
            'total': subtotal,
            'key': key,
        })

    # Remove invalid entries from session
    if to_delete:
        for key in to_delete:
            del cart[key]
        request.session.modified = True

    return items


def cart_detail(request):
    """Display the shopping cart with selection support."""
    cart_items = get_cart_items(request)
    selected_keys = request.session.get('selected_cart_keys', [])

    # Clean up selected keys that no longer exist in the cart
    valid_keys = [item['key'] for item in cart_items]
    selected_keys = [k for k in selected_keys if k in valid_keys]
    request.session['selected_cart_keys'] = selected_keys

    # Totals for all items
    total_all = sum(item['total'] for item in cart_items)
    shipping_all = get_shipping_fee(cart_items)
    grand_total_all = total_all + shipping_all

    # Totals for selected items
    selected_items = [item for item in cart_items if item['key'] in selected_keys]
    total_selected = sum(item['total'] for item in selected_items)
    shipping_selected = get_shipping_fee(selected_items)
    grand_total_selected = total_selected + shipping_selected

    context = {
        'cart_items': cart_items,
        'selected_keys': selected_keys,
        'total_all': total_all,
        'shipping_all': shipping_all,
        'grand_total_all': grand_total_all,
        'total_selected': total_selected,
        'shipping_selected': shipping_selected,
        'grand_total_selected': grand_total_selected,
    }
    return render(request, 'carts/cart_detail.html', context)


def cart_add(request, product_id):
    """
    Add a product (optionally with variant) to the cart.
    Handles POST request; expects quantity and optionally variant_id.
    """
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    variant_id = request.POST.get('variant_id')

    cart = request.session.get('cart', {})
    # Create a unique key: if variant present, use "product_id_variant_id", else just product_id
    key = f"{product_id}_{variant_id}" if variant_id else str(product_id)

    if key in cart:
        cart[key]['quantity'] += quantity
    else:
        cart[key] = {
            'product_id': product_id,
            'variant_id': variant_id if variant_id else None,
            'quantity': quantity,
        }

    request.session['cart'] = cart
    messages.success(request, f'Đã thêm {product.name} vào giỏ hàng.')
    return redirect(request.META.get('HTTP_REFERER', 'store:shop'))


def cart_update(request, key):
    """Update the quantity of an item in the cart."""
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        cart = request.session.get('cart', {})
        if key in cart:
            if quantity > 0:
                cart[key]['quantity'] = quantity
            else:
                del cart[key]
            request.session['cart'] = cart
    return redirect('carts:cart_detail')


def cart_remove(request, key):
    """Remove a single item from the cart."""
    cart = request.session.get('cart', {})
    if key in cart:
        del cart[key]
        request.session['cart'] = cart
        messages.success(request, 'Đã xóa sản phẩm khỏi giỏ hàng.')
    return redirect('carts:cart_detail')


def update_selection(request):
    """Store selected item keys in session."""
    if request.method == 'POST':
        selected_keys = request.POST.getlist('selected_items')
        request.session['selected_cart_keys'] = selected_keys
        messages.success(request, 'Đã cập nhật lựa chọn.')
    return redirect('carts:cart_detail')


def delete_selected(request):
    """Delete multiple items from the cart based on selected keys."""
    if request.method == 'POST':
        selected_keys = request.POST.getlist('selected_items')
        cart = request.session.get('cart', {})
        for key in selected_keys:
            if key in cart:
                del cart[key]
        request.session['cart'] = cart
        # Clear the selection because the items are gone
        request.session['selected_cart_keys'] = []
        messages.success(request, 'Đã xóa các sản phẩm đã chọn.')
    return redirect('carts:cart_detail')


def get_shipping_fee(cart_items):
    """
    Tính phí vận chuyển dựa trên tổng trọng lượng của các sản phẩm được chọn.
    Phí cơ bản: 20.000đ cho 1kg đầu, mỗi kg tiếp theo +10.000đ.
    Miễn phí nếu tổng trọng lượng > 5kg hoặc tổng tiền > 1.000.000đ.
    """
    total_weight = 0
    for item in cart_items:
        # Use variant weight if available, otherwise product weight
        weight = item['variant'].weight if item['variant'] and item['variant'].weight else item['product'].weight
        total_weight += weight * item['quantity']
    
    total_weight_kg = total_weight / 1000  # convert gram to kg
    total_price = sum(item['total'] for item in cart_items)
    
    # Free shipping if weight > 5kg OR total > 1,000,000 VND
    if total_weight_kg > 5 or total_price > 1000000:
        return 0
    
    # Calculate fee: 20k for first kg, 10k for each additional kg
    if total_weight_kg <= 1:
        return 20000
    else:
        return 20000 + (total_weight_kg - 1) * 10000


@login_required
def checkout(request):
    """Handle the checkout process: show form and create order."""
    cart_items = get_cart_items(request)
    if not cart_items:
        messages.error(request, "Giỏ hàng trống!")
        return redirect('carts:cart_detail')

    total = sum(item['total'] for item in cart_items)
    shipping_fee = get_shipping_fee(cart_items)  # use weight-based calculation
    grand_total = total + shipping_fee

    if request.method == 'POST':
        order = Order.objects.create(
            user=request.user,
            full_name=request.POST['full_name'],
            phone=request.POST['phone'],
            address=request.POST['address'],
            total=grand_total,
            shipping_fee=shipping_fee,
            paid=False
        )
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                variant=item.get('variant'),
                quantity=item['quantity'],
                price=item['price']
            )
        # Clear the cart after successful order
        request.session['cart'] = {}
        messages.success(request, f"Đơn hàng #{order.id} đã được đặt thành công!")
        return redirect('store:home')

    return render(request, 'carts/checkout.html', {
        'cart_items': cart_items,
        'total': total,
        'shipping_fee': shipping_fee,
        'grand_total': grand_total,
    })