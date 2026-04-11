from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Count, Q, Case, When, Value, IntegerField
from .models import Category, Product


def home(request):
    """
    Trang chủ - hiển thị danh mục nổi bật và sản phẩm hot
    """
    # Lấy danh mục nổi bật (có is_featured=True) hoặc 12 danh mục đầu tiên
    categories = Category.objects.filter(is_featured=True).annotate(
        product_count=Count('products')
    )[:12]
    
    # Nếu không có danh mục nổi bật, lấy 8 danh mục bất kỳ
    if not categories:
        categories = Category.objects.all()[:8]
    
    # Lấy sản phẩm hot (is_hot=True) hoặc mới nhất
    products = Product.objects.filter(is_hot=True, available=True)
    
    # Nếu không có sản phẩm hot, lấy 12 sản phẩm mới nhất
    if not products:
        products = Product.objects.filter(stock__gt=0).order_by('-id')[:12]
    
    return render(request, 'home.html', {
        'categories': categories,
        'products': products,
    })


def shop(request):
    """
    Trang cửa hàng với tìm kiếm, lọc giá, lọc danh mục, sắp xếp và phân trang.
    
    Query Parameters:
        q          - Từ khoá tìm kiếm (name, description, category)
        category   - Slug của danh mục
        min_price  - Giá thấp nhất
        max_price  - Giá cao nhất
        sort       - default | price_asc | price_desc | newest | sale
        page       - Số trang hiện tại
    """
    # Base queryset - chỉ lấy sản phẩm có sẵn
    qs = Product.objects.filter(available=True)
    
    # ═══════════════════════════════════════════════════════════════════
    # Lọc theo danh mục
    # ═══════════════════════════════════════════════════════════════════
    category = None
    cat_slug = request.GET.get('category', '')
    if cat_slug:
        category = get_object_or_404(Category, slug=cat_slug)
        qs = qs.filter(category=category)
    
    # ═══════════════════════════════════════════════════════════════════
    # Tìm kiếm
    # ═══════════════════════════════════════════════════════════════════
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(name__icontains=q) |
            Q(description__icontains=q) |
            Q(category__name__icontains=q)
        )
    
    # ═══════════════════════════════════════════════════════════════════
    # Lọc theo giá (sử dụng sale_price nếu có, không thì dùng price)
    # ═══════════════════════════════════════════════════════════════════
    min_price = request.GET.get('min_price', '').strip()
    max_price = request.GET.get('max_price', '').strip()
    
    if min_price:
        try:
            min_val = float(min_price)
            qs = qs.filter(
                Q(sale_price__gte=min_val) |
                Q(sale_price__isnull=True, price__gte=min_val)
            )
        except ValueError:
            pass
    
    if max_price:
        try:
            max_val = float(max_price)
            qs = qs.filter(
                Q(sale_price__lte=max_val) |
                Q(sale_price__isnull=True, price__lte=max_val)
            )
        except ValueError:
            pass
    
    # ═══════════════════════════════════════════════════════════════════
    # Sắp xếp
    # ═══════════════════════════════════════════════════════════════════
    sort = request.GET.get('sort', 'default')
    
    if sort == 'price_asc':
        # Sắp xếp theo giá tăng dần (ưu tiên sale_price)
        from django.db.models.functions import Coalesce
        from django.db.models import F
        qs = qs.annotate(
            effective_price=Coalesce('sale_price', 'price')
        ).order_by('effective_price')
        
    elif sort == 'price_desc':
        # Sắp xếp theo giá giảm dần
        from django.db.models.functions import Coalesce
        qs = qs.annotate(
            effective_price=Coalesce('sale_price', 'price')
        ).order_by('-effective_price')
        
    elif sort == 'newest':
        # Sản phẩm mới nhất
        qs = qs.order_by('-created', '-id')
        
    elif sort == 'sale':
        # Sản phẩm đang giảm giá lên đầu, sau đó mới đến mới nhất
        qs = qs.annotate(
            has_sale=Case(
                When(sale_price__isnull=False, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
        ).order_by('-has_sale', '-created', '-id')
        
    else:  # default - sắp xếp theo ID mới nhất
        qs = qs.order_by('-id')
    
    # ═══════════════════════════════════════════════════════════════════
    # Phân trang (12 sản phẩm mỗi trang)
    # ═══════════════════════════════════════════════════════════════════
    paginator = Paginator(qs, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Lấy danh sách danh mục cho sidebar filter
    categories = Category.objects.annotate(
        product_count=Count('products', filter=Q(products__available=True))
    ).filter(product_count__gt=0)
    
    return render(request, 'store/shop.html', {
        'page_obj': page_obj,
        'category': category,
        'categories': categories,
        'sort': sort,
        'search_query': q,
        'min_price': min_price,
        'max_price': max_price,
    })


def product_detail(request, slug):
    """
    Trang chi tiết sản phẩm
    """
    product = get_object_or_404(Product, slug=slug, available=True)
    
    # Lấy variants nếu có
    variants = product.variants.all()
    
    # Lấy sản phẩm liên quan (cùng danh mục, trừ sản phẩm hiện tại)
    related_products = Product.objects.filter(
        category=product.category,
        available=True
    ).exclude(id=product.id)[:8]
    
    return render(request, 'store/product_detail.html', {
        'product': product,
        'variants': variants,
        'related_products': related_products,
    })


def category_products(request, slug):
    """
    Xem sản phẩm theo danh mục (redirect sang shop với filter category)
    Hoặc có thể dùng view riêng
    """
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=category, available=True)
    
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'store/shop.html', {
        'page_obj': page_obj,
        'category': category,
        'categories': Category.objects.annotate(
            product_count=Count('products', filter=Q(products__available=True))
        ).filter(product_count__gt=0),
    })