import json, random, string
from datetime import timedelta
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import Wallet, WalletTransaction, Voucher, UserVoucher, SPIN_PRIZES


@login_required
def wallet_home(request):
    wallet = Wallet.get_or_create_for(request.user)
    transactions = wallet.transactions.all()[:20]
    vouchers = UserVoucher.objects.filter(user=request.user, used=False).select_related('voucher')
    return render(request, 'carts/wallet.html', {
        'wallet': wallet,
        'transactions': transactions,
        'vouchers': vouchers,
    })


@login_required
def wallet_topup(request):
    TOPUP_PACKAGES = [
        {'amount': 50_000, 'label': '50.000đ', 'bonus': 0},
        {'amount': 100_000, 'label': '100.000đ', 'bonus': 5_000},
        {'amount': 200_000, 'label': '200.000đ', 'bonus': 15_000},
        {'amount': 500_000, 'label': '500.000đ', 'bonus': 50_000},
        {'amount': 1_000_000, 'label': '1.000.000đ', 'bonus': 120_000},
    ]
    if request.method == 'POST':
        try:
            amount = int(request.POST.get('amount', 0))
            bonus = int(request.POST.get('bonus', 0))
            if amount <= 0:
                raise ValueError
        except (ValueError, TypeError):
            messages.error(request, 'Số tiền không hợp lệ.')
            return redirect('wallet_home')
        wallet = Wallet.get_or_create_for(request.user)
        wallet.deposit(amount, note=f'Nạp tiền — {amount:,}đ')
        if bonus > 0:
            wallet.deposit(bonus, note=f'Bonus nạp tiền — +{bonus:,}đ')
        total = amount + bonus
        messages.success(request, f'✅ Nạp thành công {total:,}đ vào ví!')
        return redirect('wallet_home')
    wallet = Wallet.get_or_create_for(request.user)
    return render(request, 'carts/topup.html', {
        'wallet': wallet,
        'packages': TOPUP_PACKAGES,
    })


@login_required
def spin_wheel(request):
    wallet = Wallet.get_or_create_for(request.user)
    SPIN_COST = 10_000
    my_vouchers = UserVoucher.objects.filter(user=request.user, used=False).select_related('voucher')
    return render(request, 'carts/spin.html', {
        'wallet': wallet,
        'spin_cost': SPIN_COST,
        'prizes': SPIN_PRIZES,
        'my_vouchers': my_vouchers,
    })


@login_required
@require_POST
def spin_wheel_api(request):
    SPIN_COST = 10_000
    wallet = Wallet.get_or_create_for(request.user)
    if wallet.balance < SPIN_COST:
        return JsonResponse({'ok': False, 'error': f'Số dư không đủ! Cần {SPIN_COST:,}đ để quay.'})
    wallet.spend(SPIN_COST, note='Vòng quay may mắn')
    weights = [p['weight'] for p in SPIN_PRIZES]
    prize_idx = random.choices(range(len(SPIN_PRIZES)), weights=weights, k=1)[0]
    prize = SPIN_PRIZES[prize_idx]
    result_msg = ''
    voucher_code = ''
    if prize['type'] == 'voucher':
        code = 'SPIN' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        voucher = Voucher.objects.create(
            code=code,
            type=prize['vtype'],
            value=prize['value'],
            min_order=50_000,
            max_discount=200_000 if prize['vtype'] == 'percent' else None,
            is_active=True,
            is_spin=True,
            expires_at=timezone.now() + timedelta(days=7),
        )
        UserVoucher.objects.create(user=request.user, voucher=voucher)
        voucher_code = code
        if prize['vtype'] == 'percent':
            result_msg = f'Bạn trúng voucher giảm {prize["value"]}%! 🎉'
        else:
            result_msg = f'Bạn trúng voucher giảm {prize["value"]:,}đ! 🎉'
        WalletTransaction.objects.create(
            wallet=wallet, amount=0,
            type='reward',
            note=f'Trúng voucher {code} từ vòng quay'
        )
    else:
        result_msg = 'Chúc bạn may mắn lần sau! 🎲'
    return JsonResponse({
        'ok': True,
        'prize_idx': prize_idx,
        'prize_label': prize['label'],
        'result_msg': result_msg,
        'voucher_code': voucher_code,
        'new_balance': int(wallet.balance),
    })


@login_required
@require_POST
def apply_voucher_api(request):
    data = json.loads(request.body)
    code = data.get('code', '').strip().upper()
    total = int(data.get('total', 0))
    try:
        voucher = Voucher.objects.get(code=code, is_active=True)
    except Voucher.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Mã voucher không hợp lệ hoặc đã hết hạn.'})
    if voucher.is_spin:
        if not UserVoucher.objects.filter(user=request.user, voucher=voucher, used=False).exists():
            return JsonResponse({'ok': False, 'error': 'Voucher này không thuộc về bạn.'})
    if voucher.expires_at and voucher.expires_at < timezone.now():
        return JsonResponse({'ok': False, 'error': 'Voucher đã hết hạn.'})
    discount = voucher.calc_discount(total)
    if discount == 0:
        return JsonResponse({'ok': False, 'error': f'Đơn hàng tối thiểu {voucher.min_order:,}đ để dùng voucher này.'})
    return JsonResponse({
        'ok': True,
        'code': voucher.code,
        'discount': discount,
        'label': str(voucher),
        'new_total': max(0, total - discount),
    })