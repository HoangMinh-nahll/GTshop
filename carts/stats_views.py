from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count, F
from django.utils import timezone
from datetime import timedelta, date
from .models import Order, OrderItem
import json


@staff_member_required  # Chỉ admin/staff mới xem được
def stats_dashboard(request):
    today     = timezone.now().date()
    this_month_start = today.replace(day=1)
    last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
    last_month_end   = this_month_start - timedelta(days=1)

    revenue_today = Order.objects.filter(
        created__date=today
    ).aggregate(total=Sum('total'))['total'] or 0

    orders_today = Order.objects.filter(created__date=today).count()

    revenue_month = Order.objects.filter(
        created__date__gte=this_month_start
    ).aggregate(total=Sum('total'))['total'] or 0

    orders_month = Order.objects.filter(
        created__date__gte=this_month_start
    ).count()

    revenue_last_month = Order.objects.filter(
        created__date__gte=last_month_start,
        created__date__lte=last_month_end
    ).aggregate(total=Sum('total'))['total'] or 0

    if revenue_last_month > 0:
        revenue_growth = ((revenue_month - revenue_last_month) / revenue_last_month) * 100
    else:
        revenue_growth = 100.0

    orders_paid    = Order.objects.filter(paid=True).count()
    orders_pending = Order.objects.filter(paid=False).count()

    from django.contrib.auth.models import User
    total_users     = User.objects.filter(is_staff=False).count()
    new_users_month = User.objects.filter(
        date_joined__date__gte=this_month_start,
        is_staff=False
    ).count()

    top_products = OrderItem.objects.values(
        'product__name'
    ).annotate(
        total_qty=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('price'))
    ).order_by('-total_qty')[:5]

    revenue_labels = []
    revenue_data   = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        label = d.strftime('%d/%m')
        rev = Order.objects.filter(
            created__date=d
        ).aggregate(total=Sum('total'))['total'] or 0
        revenue_labels.append(label)
        revenue_data.append(float(rev))

    recent_orders = Order.objects.select_related('user').order_by('-created')[:10]

    context = {
        'revenue_today':    revenue_today,
        'orders_today':     orders_today,
        'revenue_month':    revenue_month,
        'orders_month':     orders_month,
        'revenue_growth':   revenue_growth,
        'orders_paid':      orders_paid,
        'orders_pending':   orders_pending,
        'total_users':      total_users,
        'new_users_month':  new_users_month,
        'top_products':     top_products,
        'recent_orders':    recent_orders,
        'revenue_labels':   json.dumps(revenue_labels),
        'revenue_data':     json.dumps(revenue_data),
    }
    return render(request, 'stats/dashboard.html', context)