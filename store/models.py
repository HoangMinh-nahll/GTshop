from django.db import models
from django.urls import reverse


class Category(models.Model):
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_featured = models.BooleanField(default=False, help_text="Hiển thị trên trang chủ")

    class Meta:
        ordering = ('name',)
        verbose_name = 'danh mục'
        verbose_name_plural = 'danh mục'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('store:category_products', args=[self.slug])


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=200, unique=True, db_index=True)
    image = models.ImageField(upload_to='products/', blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Giá gốc")
    sale_price = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True, verbose_name="Giá khuyến mãi")
    stock = models.PositiveIntegerField(default=0)
    available = models.BooleanField(default=True)
    is_hot = models.BooleanField(default=False, help_text="Sản phẩm hot hiển thị trên trang chủ")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    weight = models.PositiveIntegerField(default=0, verbose_name="Cân nặng (gram)", help_text="Dùng để tính phí vận chuyển")

    class Meta:
        ordering = ('name',)
        verbose_name = 'sản phẩm'
        verbose_name_plural = 'sản phẩm'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('store:product_detail', args=[self.slug])

    def get_discount_percent(self):
        if self.sale_price and self.price > 0:
            return int(100 - (self.sale_price * 100 / self.price))
        return 0


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    name = models.CharField(max_length=100, verbose_name="Tên biến thể", help_text="VD: 100ml, Màu đỏ...")
    price = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True, verbose_name="Giá (nếu khác giá gốc)")
    stock = models.PositiveIntegerField(default=0, verbose_name="Tồn kho")
    image = models.ImageField(upload_to='variants/', blank=True, null=True, verbose_name="Ảnh riêng (nếu có)")
    weight = models.PositiveIntegerField(default=0, verbose_name="Cân nặng (gram)", help_text="Nếu để trống sẽ lấy từ sản phẩm gốc")

    class Meta:
        verbose_name = "Biến thể sản phẩm"
        verbose_name_plural = "Biến thể sản phẩm"

    def __str__(self):
        return f"{self.product.name} - {self.name}"