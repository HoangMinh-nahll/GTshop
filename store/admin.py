from django.contrib import admin
from .models import Category, Product, ProductVariant


# ===================== INLINE CHO BIẾN THỂ SẢN PHẨM =====================
class ProductVariantInline(admin.TabularInline):
    """
    Cho phép thêm/sửa biến thể (size, màu, dung tích...) ngay trong trang sửa sản phẩm.
    """
    model = ProductVariant
    extra = 1                         # số dòng trống để thêm mới
    fields = ('name', 'price', 'stock', 'image')
    show_change_link = True           # hiển thị link đến trang chi tiết biến thể


# ===================== QUẢN TRỊ SẢN PHẨM =====================
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Quản lý sản phẩm: hiển thị danh sách, bộ lọc, chỉnh sửa nhanh,
    tự động tạo slug, và kèm inline biến thể.
    """
    list_display = ('name', 'slug', 'price', 'stock', 'available', 'created', 'updated')
    list_filter = ('available', 'created', 'updated', 'category')
    list_editable = ('price', 'stock', 'available')   # cho phép sửa trực tiếp trên danh sách
    prepopulated_fields = {'slug': ('name',)}         # tự động tạo slug từ tên
    inlines = [ProductVariantInline]                  # hiển thị các biến thể bên dưới


# ===================== QUẢN TRỊ BIẾN THỂ SẢN PHẨM =====================
@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    """
    Quản lý riêng các biến thể (size, màu, dung tích...).
    """
    list_display = ('product', 'name', 'price', 'stock')
    list_filter = ('product',)
    search_fields = ('name',)


# ===================== QUẢN TRỊ DANH MỤC =====================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Quản lý danh mục sản phẩm.
    """
    prepopulated_fields = {'slug': ('name',)}      # tự động tạo slug từ tên danh mục
    list_display = ('name', 'is_featured')          # hiển thị tên và trạng thái nổi bật
    list_filter = ('is_featured',)                 # bộ lọc theo trạng thái nổi bật
    search_fields = ('name',)                      # tìm kiếm theo tên