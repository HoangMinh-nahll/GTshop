from django.db import models
from django.contrib.auth.models import User
from store.models import Product, ProductVariant


# ─── Giỏ hàng lưu theo tài khoản (như Shopee) ────────────────────────────────
class SavedCartItem(models.Model):
    """
    Lưu giỏ hàng của user vào database.
    - Khi đăng nhập: load từ DB vào session
    - Khi thêm hàng (đang login): lưu cả session lẫn DB
    - Khi đăng xuất: xóa session, DB giữ nguyên
    """
    user     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_cart_items')
    product  = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant  = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product', 'variant')
        verbose_name = 'Giỏ hàng đã lưu'
        verbose_name_plural = 'Giỏ hàng đã lưu'

    def __str__(self):
        return f"{self.user.username} — {self.product.name} x{self.quantity}"

    @staticmethod
    def session_key(product_id, variant_id=None):
        """Tạo key giống format session cart"""
        return f"{product_id}_{variant_id}" if variant_id else str(product_id)

    @classmethod
    def load_to_session(cls, user, request):
        """Load giỏ hàng từ DB vào session khi đăng nhập"""
        db_items = cls.objects.filter(user=user).select_related('product', 'variant')
        if not db_items.exists():
            return

        session_cart = request.session.get('cart', {})

        for item in db_items:
            key = cls.session_key(item.product_id, item.variant_id)
            if key in session_cart:
                # Lấy số lượng lớn hơn (ưu tiên DB nếu nhiều hơn)
                session_cart[key]['quantity'] = max(
                    session_cart[key]['quantity'],
                    item.quantity
                )
            else:
                session_cart[key] = {
                    'product_id': item.product_id,
                    'variant_id': item.variant_id,
                    'quantity':   item.quantity,
                }

        request.session['cart'] = session_cart
        request.session.modified = True

    @classmethod
    def save_from_session(cls, user, request):
        """Lưu toàn bộ session cart vào DB (gọi khi logout)"""
        session_cart = request.session.get('cart', {})
        for key, data in session_cart.items():
            try:
                variant_id = data.get('variant_id')
                variant = ProductVariant.objects.get(id=variant_id) if variant_id else None

                obj, created = cls.objects.get_or_create(
                    user=user,
                    product_id=data['product_id'],
                    variant=variant,
                    defaults={'quantity': data['quantity']}
                )
                if not created:
                    obj.quantity = data['quantity']
                    obj.save()
            except Exception:
                continue

    @classmethod
    def sync_item(cls, user, product_id, variant_id, quantity):
        """Đồng bộ 1 item vào DB ngay khi user thêm/cập nhật giỏ hàng"""
        if quantity <= 0:
            cls.objects.filter(
                user=user,
                product_id=product_id,
                variant_id=variant_id
            ).delete()
            return
        try:
            variant = ProductVariant.objects.get(id=variant_id) if variant_id else None
            obj, created = cls.objects.get_or_create(
                user=user,
                product_id=product_id,
                variant=variant,
                defaults={'quantity': quantity}
            )
            if not created:
                obj.quantity = quantity
                obj.save()
        except Exception:
            pass

    @classmethod
    def remove_item(cls, user, product_id, variant_id=None):
        """Xóa item khỏi DB khi user xóa khỏi giỏ"""
        cls.objects.filter(
            user=user,
            product_id=product_id,
            variant_id=variant_id
        ).delete()


# ─── Order models (giữ nguyên từ trước) ──────────────────────────────────────
class Order(models.Model):
    user         = models.ForeignKey(User, on_delete=models.CASCADE)
    full_name    = models.CharField(max_length=100, verbose_name="Họ tên")
    phone        = models.CharField(max_length=20, verbose_name="Số điện thoại")
    address      = models.TextField(verbose_name="Địa chỉ")
    total        = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name="Tổng tiền")
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name="Phí vận chuyển")
    paid         = models.BooleanField(default=False, verbose_name="Đã thanh toán")
    created      = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")

    class Meta:
        verbose_name = "Đơn hàng"
        verbose_name_plural = "Đơn hàng"

    def __str__(self):
        return f"Đơn hàng #{self.id} - {self.user.username}"


class OrderItem(models.Model):
    order    = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product  = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant  = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    price    = models.DecimalField(max_digits=10, decimal_places=0)

    class Meta:
        verbose_name = "Chi tiết đơn hàng"
        verbose_name_plural = "Chi tiết đơn hàng"

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"