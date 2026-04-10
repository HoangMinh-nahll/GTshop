"""
Giỏ hàng hoạt động như Shopee:

  ĐĂNG NHẬP  → Load giỏ hàng từ DB của tài khoản vào session
  MUA SẮM    → Mỗi lần thêm/sửa/xóa đều sync ngay vào DB
  ĐĂNG XUẤT  → Lưu DB lần cuối, xóa session → giỏ trống
  ĐĂNG NHẬP LẠI → Load DB → thấy lại đúng giỏ hàng cũ
"""

from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver


@receiver(user_logged_in)
def load_cart_on_login(sender, request, user, **kwargs):
    """Khi đăng nhập: load giỏ hàng từ DB vào session"""
    from carts.models import SavedCartItem
    SavedCartItem.load_to_session(user, request)


@receiver(user_logged_out)
def save_cart_on_logout(sender, request, user, **kwargs):
    """
    Khi đăng xuất: lưu session cart vào DB trước khi session bị xóa.
    Signal này chạy TRƯỚC khi Django flush session.
    """
    if user and request:
        from carts.models import SavedCartItem
        SavedCartItem.save_from_session(user, request)