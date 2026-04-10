from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from store.models import Product, ProductVariant
from .models import Order, OrderItem, SavedCartItem


# ─── Helper: sync 1 item vào DB nếu user đang đăng nhập ─────────────────────
def _sync_to_db(request, product_id, variant_id, quantity):
    if request.user.is_authenticated:
        SavedCartItem.sync_item(request.user, product_id, variant_id, quantity)


def _remove_from_db(request, product_id, variant_id=None):
    if request.user.is_authenticated:
        SavedCartItem.remove_item(request.user, product_id, variant_id)


# ─── Lấy tất cả item từ session ─────────────────────────────────────────────
def get_cart_items(request):
    cart = request.session.get('cart', {})
    items = []
    product_ids, variant_ids = [], []

    for key, data in cart.items():
        product_ids.append(data['product_id'])
        if data.get('variant_id'):
            variant_ids.append(int(data['variant_id']))

    products = Product.objects.filter(id__in=product_ids)
    variants = ProductVariant.objects.filter(id__in=variant_ids) if variant_ids else []
    product_dict = {p.id: p for p in products}
    variant_dict = {v.id: v for v in variants}

    to_delete = []
    for key, data in cart.items():
        product = product_dict.get(data['product_id'])
        if not product:
            to_delete.append(key)
            continue

        variant = None
        if data.get('variant_id'):
            try:
                variant = variant_dict.get(int(data['variant_id']))
            except (ValueError, TypeError):
                variant = None
            if not variant:
                to_delete.append(key)
                continue

        price    = variant.price if variant and variant.price else product.price
        subtotal = price * data['quantity']
        items.append({
            'product':  product,
            'variant':  variant,
            'quantity': data['quantity'],
            'price':    price,
            'total':    subtotal,
            'key':      key,
        })

    if to_delete:
        for key in to_delete:
            del cart[key]
        request.session.modified = True

    return items


# ─── Hiển thị giỏ hàng ───────────────────────────────────────────────────────
def cart_detail(request):
    cart_items    = get_cart_items(request)
    selected_keys = request.session.get('selected_cart_keys', [])
    valid_keys    = [item['key'] for item in cart_items]
    selected_keys = [k for k in selected_keys if k in valid_keys]
    request.session['selected_cart_keys'] = selected_keys

    total_all        = sum(item['total'] for item in cart_items)
    shipping_all     = get_shipping_fee(cart_items)
    grand_total_all  = total_all + shipping_all

    selected_items        = [item for item in cart_items if item['key'] in selected_keys]
    total_selected        = sum(item['total'] for item in selected_items)
    shipping_selected     = get_shipping_fee(selected_items)
    grand_total_selected  = total_selected + shipping_selected

    return render(request, 'carts/cart_detail.html', {
        'cart_items':           cart_items,
        'selected_keys':        selected_keys,
        'total_all':            total_all,
        'shipping_all':         shipping_all,
        'grand_total_all':      grand_total_all,
        'total_selected':       total_selected,
        'shipping_selected':    shipping_selected,
        'grand_total_selected': grand_total_selected,
    })


# ─── Thêm vào giỏ ────────────────────────────────────────────────────────────
def cart_add(request, product_id):
    product    = get_object_or_404(Product, id=product_id)
    quantity   = int(request.POST.get('quantity', 1))
    variant_id = request.POST.get('variant_id')

    cart = request.session.get('cart', {})
    key  = f"{product_id}_{variant_id}" if variant_id else str(product_id)

    if key in cart:
        cart[key]['quantity'] += quantity
    else:
        cart[key] = {
            'product_id': product_id,
            'variant_id': variant_id if variant_id else None,
            'quantity':   quantity,
        }

    request.session['cart'] = cart

    # ── Sync vào DB nếu đang đăng nhập ──
    _sync_to_db(request, product_id, variant_id, cart[key]['quantity'])

    messages.success(request, f'Đã thêm {product.name} vào giỏ hàng.')
    return redirect(request.META.get('HTTP_REFERER', 'store:shop'))


# ─── Cập nhật số lượng ───────────────────────────────────────────────────────
def cart_update(request, key):
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        cart     = request.session.get('cart', {})

        if key in cart:
            if quantity > 0:
                cart[key]['quantity'] = quantity
                # Sync vào DB
                _sync_to_db(
                    request,
                    cart[key]['product_id'],
                    cart[key].get('variant_id'),
                    quantity
                )
            else:
                _remove_from_db(request, cart[key]['product_id'], cart[key].get('variant_id'))
                del cart[key]
            request.session['cart'] = cart

    return redirect('carts:cart_detail')


# ─── Xóa 1 item ──────────────────────────────────────────────────────────────
def cart_remove(request, key):
    cart = request.session.get('cart', {})
    if key in cart:
        _remove_from_db(request, cart[key]['product_id'], cart[key].get('variant_id'))
        del cart[key]
        request.session['cart'] = cart
        messages.success(request, 'Đã xóa sản phẩm khỏi giỏ hàng.')
    return redirect('carts:cart_detail')


# ─── Cập nhật lựa chọn ───────────────────────────────────────────────────────
def update_selection(request):
    if request.method == 'POST':
        request.session['selected_cart_keys'] = request.POST.getlist('selected_items')
        messages.success(request, 'Đã cập nhật lựa chọn.')
    return redirect('carts:cart_detail')


# ─── Xóa các item đã chọn ────────────────────────────────────────────────────
def delete_selected(request):
    if request.method == 'POST':
        selected_keys = request.POST.getlist('selected_items')
        cart = request.session.get('cart', {})
        for key in selected_keys:
            if key in cart:
                _remove_from_db(request, cart[key]['product_id'], cart[key].get('variant_id'))
                del cart[key]
        request.session['cart'] = cart
        request.session['selected_cart_keys'] = []
        messages.success(request, 'Đã xóa các sản phẩm đã chọn.')
    return redirect('carts:cart_detail')


# ─── Tính phí ship ───────────────────────────────────────────────────────────
def get_shipping_fee(cart_items):
    total_weight = 0
    for item in cart_items:
        weight = (
            item['variant'].weight
            if item['variant'] and item['variant'].weight
            else item['product'].weight
        )
        total_weight += weight * item['quantity']

    total_weight_kg = total_weight / 1000
    total_price     = sum(item['total'] for item in cart_items)

    if total_weight_kg > 5 or total_price > 1_000_000:
        return 0
    if total_weight_kg <= 1:
        return 20_000
    return 20_000 + (total_weight_kg - 1) * 10_000


# ─── Checkout ────────────────────────────────────────────────────────────────
@login_required
def checkout(request):
    cart_items = get_cart_items(request)
    if not cart_items:
        messages.error(request, 'Giỏ hàng trống!')
        return redirect('carts:cart_detail')

    total        = sum(item['total'] for item in cart_items)
    shipping_fee = get_shipping_fee(cart_items)
    grand_total  = total + shipping_fee

    if request.method == 'POST':
        order = Order.objects.create(
            user=request.user,
            full_name=request.POST['full_name'],
            phone=request.POST['phone'],
            address=request.POST['address'],
            total=grand_total,
            shipping_fee=shipping_fee,
            paid=False,
        )
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                variant=item.get('variant'),
                quantity=item['quantity'],
                price=item['price'],
            )

        # Xóa giỏ hàng session + DB sau khi đặt hàng thành công
        request.session['cart'] = {}
        if request.user.is_authenticated:
            SavedCartItem.objects.filter(user=request.user).delete()

        messages.success(request, f'Đơn hàng #{order.id} đã được đặt thành công!')
        return redirect('store:home')

    return render(request, 'carts/checkout.html', {
        'cart_items':   cart_items,
        'total':        total,
        'shipping_fee': shipping_fee,
        'grand_total':  grand_total,
    })