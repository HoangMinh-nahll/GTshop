from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from django.db.models import Avg, Count
from .review_models import ProductReview


@login_required
@require_POST
def submit_review(request, product_id):
    """Gửi hoặc cập nhật đánh giá — trả về JSON"""
    from .models import Product
    product = get_object_or_404(Product, id=product_id)

    rating  = int(request.POST.get('rating', 0))
    title   = request.POST.get('title', '').strip()
    comment = request.POST.get('comment', '').strip()
    image   = request.FILES.get('image')

    if not (1 <= rating <= 5):
        return JsonResponse({'ok': False, 'error': 'Vui lòng chọn số sao.'}, status=400)
    if not comment:
        return JsonResponse({'ok': False, 'error': 'Vui lòng nhập nội dung.'}, status=400)

    # Kiểm tra đã mua hàng chưa
    from carts.models import OrderItem
    is_verified = OrderItem.objects.filter(
        order__user=request.user,
        product=product,
    ).exists()

    review, created = ProductReview.objects.update_or_create(
        product=product,
        user=request.user,
        defaults={
            'rating':               rating,
            'title':                title,
            'comment':              comment,
            'is_verified_purchase': is_verified,
        }
    )

    if image:
        review.image = image
        review.save()

    # Tính lại rating trung bình
    agg   = product.reviews.aggregate(avg=Avg('rating'), cnt=Count('id'))
    avg_r = round(agg['avg'] or 0, 1)
    cnt_r = agg['cnt']

    return JsonResponse({
        'ok':       True,
        'created':  created,
        'review': {
            'id':        review.id,
            'username':  request.user.username,
            'rating':    review.rating,
            'title':     review.title,
            'comment':   review.comment,
            'image_url': review.image.url if review.image else '',
            'verified':  review.is_verified_purchase,
            'date':      review.created.strftime('%d/%m/%Y'),
        },
        'avg_rating': avg_r,
        'total':      cnt_r,
    })


@login_required
@require_POST
def delete_review(request, review_id):
    """Xóa đánh giá của mình"""
    review = get_object_or_404(ProductReview, id=review_id, user=request.user)
    product = review.product
    review.delete()

    agg   = product.reviews.aggregate(avg=Avg('rating'), cnt=Count('id'))
    avg_r = round(agg['avg'] or 0, 1)
    cnt_r = agg['cnt']

    return JsonResponse({'ok': True, 'avg_rating': avg_r, 'total': cnt_r})