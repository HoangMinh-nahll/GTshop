from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages


def merge_session_cart(request, old_session_key=None):
    """
    Sau khi đăng nhập: giữ lại giỏ hàng session cũ (trước login).
    Django tự tạo session mới khi login → cần chuyển cart sang session mới.
    """
    if not old_session_key:
        return

    from django.contrib.sessions.backends.db import SessionStore
    try:
        old_session = SessionStore(session_key=old_session_key)
        old_cart = old_session.get('cart', {})
    except Exception:
        return

    if not old_cart:
        return

    # Lấy giỏ hàng hiện tại của session mới (nếu có)
    current_cart = request.session.get('cart', {})

    # Merge: nếu cùng key thì cộng số lượng
    for key, data in old_cart.items():
        if key in current_cart:
            current_cart[key]['quantity'] += data['quantity']
        else:
            current_cart[key] = data

    request.session['cart'] = current_cart
    request.session.modified = True


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            # Lưu session key cũ trước khi tạo user
            old_session_key = request.session.session_key

            user = form.save()
            login(request, user)

            # Chuyển giỏ hàng từ session cũ sang session mới
            merge_session_cart(request, old_session_key)

            messages.success(request, f'Tài khoản {user.username} đã được tạo thành công!')
            return redirect('store:home')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})