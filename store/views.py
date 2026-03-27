from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Count
from .models import Category, Product

def home(request):
    categories = Category.objects.filter(is_featured=True).annotate(
        product_count=Count('products')
    )[:12]
    products = Product.objects.filter(is_hot=True, available=True)  # không giới hạn
    return render(request, 'home.html', {'categories': categories, 'products': products})

def shop(request):
    products = Product.objects.filter(available=True).order_by('-created')
    query = request.GET.get('q')
    if query:
        products = products.filter(name__icontains=query)

    paginator = Paginator(products, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'shop.html', {'page_obj': page_obj})

def category_products(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=category, available=True)
    paginator = Paginator(products, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'shop.html', {
        'page_obj': page_obj,
        'category': category,
    })

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, available=True)
    variants = product.variants.all()
    return render(request, 'store/product_detail.html', {
        'product': product,
        'variants': variants,
    })