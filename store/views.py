from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, Case, When, Value, IntegerField, Avg, Count
from .models import Product, Category
from .review_models import ProductReview


def home(request):
    # Lấy danh mục kèm số lượng sản phẩm (từ đoạn code thứ hai)
    categories = Category.objects.annotate(product_count=Count('products')).order_by('name')
    products   = Product.objects.filter(stock__gt=0).order_by('-id')[:12]
    return render(request, 'home.html', {
        'categories': categories,
        'products':   products,
    })


def shop(request):
    qs = Product.objects.all()

    # Tìm kiếm
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(name__icontains=q) |
            Q(description__icontains=q) |
            Q(category__name__icontains=q)
        )

    # Lọc giá
    min_price = request.GET.get('min_price', '').strip()
    max_price = request.GET.get('max_price', '').strip()
    if min_price:
        try:
            qs = qs.filter(
                Q(sale_price__gte=float(min_price)) |
                Q(sale_price__isnull=True, price__gte=float(min_price))
            )
        except ValueError:
            pass
    if max_price:
        try:
            qs = qs.filter(
                Q(sale_price__lte=float(max_price)) |
                Q(sale_price__isnull=True, price__lte=float(max_price))
            )
        except ValueError:
            pass

    # Sắp xếp
    sort = request.GET.get('sort', 'default')
    if sort == 'price_asc':
        qs = qs.extra(select={'ep': 'COALESCE(sale_price, price)'}).order_by('ep')
    elif sort == 'price_desc':
        qs = qs.extra(select={'ep': 'COALESCE(sale_price, price)'}).order_by('-ep')
    elif sort == 'newest':
        qs = qs.order_by('-created')
    elif sort == 'sale':
        qs = qs.annotate(
            has_sale=Case(
                When(sale_price__isnull=False, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
        ).order_by('-has_sale', '-created')
    else:
        qs = qs.order_by('-id')

    paginator   = Paginator(qs, 12)
    page_obj    = paginator.get_page(request.GET.get('page', 1))
    category    = None
    cat_slug    = request.GET.get('category', '')
    if cat_slug:
        category = get_object_or_404(Category, slug=cat_slug)

    return render(request, 'store/shop.html', {
        'page_obj': page_obj,
        'category': category,
        'sort':     sort,
    })


def product_detail(request, slug):
    product  = get_object_or_404(Product, slug=slug)
    variants = product.variants.all()

    # ── Reviews ─────────────────────────────────────
    reviews = ProductReview.objects.filter(
        product=product
    ).select_related('user').order_by('-created')

    agg        = reviews.aggregate(avg=Avg('rating'), cnt=Count('id'))
    avg_rating = round(agg['avg'] or 0, 1)
    total_reviews = agg['cnt']

    # Phân bổ sao (1-5)
    star_dist = {}
    for i in range(1, 6):
        cnt = reviews.filter(rating=i).count()
        star_dist[i] = {
            'count': cnt,
            'pct': round(cnt / total_reviews * 100) if total_reviews else 0,
        }

    # Kiểm tra user đã review chưa
    user_review = None
    if request.user.is_authenticated:
        user_review = reviews.filter(user=request.user).first()

    # Kiểm tra đã mua hàng chưa
    has_purchased = False
    if request.user.is_authenticated:
        from carts.models import OrderItem
        has_purchased = OrderItem.objects.filter(
            order__user=request.user,
            product=product,
        ).exists()

    return render(request, 'store/product_detail.html', {
        'product':       product,
        'variants':      variants,
        'reviews':       reviews,
        'avg_rating':    avg_rating,
        'total_reviews': total_reviews,
        'star_dist':     star_dist,
        'user_review':   user_review,
        'has_purchased': has_purchased,
    })


def category_products(request, slug):
    """
    Xem sản phẩm theo danh mục (dùng riêng, tương thích với urls.py)
    """
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=category, available=True)

    paginator = Paginator(products, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Lấy danh sách danh mục cho sidebar (giống shop)
    categories = Category.objects.annotate(
        product_count=Count('products', filter=Q(products__available=True))
    ).filter(product_count__gt=0)

    return render(request, 'store/shop.html', {
        'page_obj': page_obj,
        'category': category,
        'categories': categories,
    })