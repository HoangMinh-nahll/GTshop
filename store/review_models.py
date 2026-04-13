from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class ProductReview(models.Model):
    STAR_CHOICES = [(i, i) for i in range(1, 6)]

    product  = models.ForeignKey(
        'store.Product', on_delete=models.CASCADE, related_name='reviews'
    )
    user     = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='reviews'
    )
    rating   = models.PositiveSmallIntegerField(
        choices=STAR_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Số sao"
    )
    title    = models.CharField(max_length=100, blank=True, verbose_name="Tiêu đề")
    comment  = models.TextField(verbose_name="Nội dung bình luận")
    image    = models.ImageField(
        upload_to='reviews/', blank=True, null=True, verbose_name="Ảnh đính kèm"
    )
    is_verified_purchase = models.BooleanField(
        default=False, verbose_name="Đã mua hàng"
    )
    created  = models.DateTimeField(auto_now_add=True)
    updated  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Đánh giá sản phẩm"
        verbose_name_plural = "Đánh giá sản phẩm"
        unique_together     = ('product', 'user')
        ordering            = ['-created']

    def __str__(self):
        return f"{self.user.username} — {self.product.name} ({self.rating}★)"