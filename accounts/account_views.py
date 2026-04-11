import json
import urllib.request
import urllib.error
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from carts.models import Order


# ═══════════════════════════════════════════════════════
# MY ACCOUNT
# ═══════════════════════════════════════════════════════
@login_required
def my_account(request):
    tab = request.GET.get('tab', 'orders')

    if request.method == 'POST':
        action = request.POST.get('action', '')

        # ── Cập nhật thông tin cá nhân ──────────────────
        if action == 'update_profile':
            user = request.user
            user.email      = request.POST.get('email', '').strip()
            user.first_name = request.POST.get('first_name', '').strip()
            user.save()
            messages.success(request, '✅ Đã cập nhật thông tin thành công!')
            return redirect('/accounts/me/?tab=profile')

        # ── Đổi mật khẩu ────────────────────────────────
        elif action == 'change_password':
            user    = request.user
            old_pw  = request.POST.get('old_password', '')
            new_pw1 = request.POST.get('new_password1', '')
            new_pw2 = request.POST.get('new_password2', '')

            if not user.check_password(old_pw):
                messages.error(request, '❌ Mật khẩu hiện tại không đúng.')
            elif new_pw1 != new_pw2:
                messages.error(request, '❌ Mật khẩu mới không khớp.')
            elif len(new_pw1) < 8:
                messages.error(request, '❌ Mật khẩu mới phải có ít nhất 8 ký tự.')
            else:
                user.set_password(new_pw1)
                user.save()
                update_session_auth_hash(request, user)
                messages.success(request, '✅ Đổi mật khẩu thành công!')
            return redirect('/accounts/me/?tab=password')

    # ── Lấy đơn hàng ────────────────────────────────────
    orders = Order.objects.filter(
        user=request.user
    ).prefetch_related(
        'items__product',
        'items__variant',
    ).order_by('-created')

    return render(request, 'account/account.html', {
        'tab':    tab,
        'orders': orders,
    })


# ═══════════════════════════════════════════════════════
# CHATBOT API PROXY
# Gọi Anthropic từ backend → bảo mật API key
# ═══════════════════════════════════════════════════════
@require_POST
def chatbot_api(request):
    try:
        body = json.loads(request.body)
        user_message  = body.get('message', '').strip()
        history       = body.get('history', [])   # [{role, content}, ...]

        if not user_message:
            return JsonResponse({'error': 'empty message'}, status=400)

        # Lấy API key từ settings hoặc env
        api_key = getattr(settings, 'ANTHROPIC_API_KEY', '')
        if not api_key:
            import os
            api_key = os.environ.get('ANTHROPIC_API_KEY', '')

        if not api_key:
            # Fallback: trả lời cứng nếu không có API key
            reply = _fallback_reply(user_message)
            return JsonResponse({'reply': reply})

        # Build messages (giới hạn 10 lượt gần nhất)
        msgs = []
        for h in history[-10:]:
            if h.get('role') in ('user', 'assistant') and h.get('content'):
                msgs.append({'role': h['role'], 'content': h['content']})
        msgs.append({'role': 'user', 'content': user_message})

        payload = json.dumps({
            'model': 'claude-haiku-4-5-20251001',
            'max_tokens': 400,
            'system': (
                'Bạn là trợ lý bán hàng thân thiện của GTShop — siêu thị trực tuyến Việt Nam.\n'
                'Nhiệm vụ: tư vấn sản phẩm, hỗ trợ đơn hàng, vận chuyển, đổi trả.\n'
                'Thông tin:\n'
                '- Miễn phí ship đơn trên 500,000đ\n'
                '- Đổi trả 30 ngày miễn phí\n'
                '- Giao hàng 2h nội thành\n'
                '- Thanh toán: COD hoặc chuyển khoản\n'
                '- Hotline: 1800-1234\n'
                'Trả lời ngắn (dưới 100 từ), thân thiện, có emoji. '
                'Trả lời cùng ngôn ngữ người dùng đang dùng.'
            ),
            'messages': msgs,
        }).encode('utf-8')

        req = urllib.request.Request(
            'https://api.anthropic.com/v1/messages',
            data=payload,
            headers={
                'Content-Type':      'application/json',
                'x-api-key':         api_key,
                'anthropic-version': '2023-06-01',
            },
            method='POST',
        )
        with urllib.request.urlopen(req, timeout=15) as res:
            data  = json.loads(res.read().decode('utf-8'))
            reply = data['content'][0]['text']

        return JsonResponse({'reply': reply})

    except urllib.error.HTTPError as e:
        err = e.read().decode('utf-8')
        return JsonResponse({'reply': _fallback_reply(user_message)})
    except Exception as e:
        return JsonResponse({'reply': _fallback_reply('')})


def _fallback_reply(msg: str) -> str:
    """Trả lời cứng khi không có API key (demo mode)"""
    msg_lower = msg.lower()
    if any(w in msg_lower for w in ['ship', 'vận chuyển', 'giao hàng', 'phí']):
        return '🚚 Miễn phí vận chuyển cho đơn hàng trên 500.000đ! Giao 2h nội thành, 1-3 ngày toàn quốc.'
    if any(w in msg_lower for w in ['đổi trả', 'trả hàng', 'hoàn tiền', 'return']):
        return '🔄 Chính sách đổi trả 30 ngày miễn phí! Sản phẩm lỗi hoặc không đúng mô tả sẽ được hoàn tiền 100%.'
    if any(w in msg_lower for w in ['thanh toán', 'payment', 'cod', 'chuyển khoản']):
        return '💳 GTShop hỗ trợ thanh toán COD (khi nhận hàng) và chuyển khoản ngân hàng. An toàn 100%!'
    if any(w in msg_lower for w in ['giờ', 'làm việc', 'liên hệ', 'hotline', 'support']):
        return '🎧 Hotline 1800-1234 (miễn phí), hỗ trợ 24/7. Email: support@gtshop.vn'
    if any(w in msg_lower for w in ['sale', 'giảm giá', 'khuyến mãi', 'discount']):
        return '🔥 Flash Sale mỗi ngày! Giảm đến 50% cho sản phẩm hot. Xem tại trang Cửa hàng nhé!'
    if any(w in msg_lower for w in ['xin chào', 'hello', 'hi', 'chào']):
        return '👋 Xin chào! Tôi là trợ lý GTShop. Tôi có thể giúp bạn tìm sản phẩm, hỏi về vận chuyển, đổi trả. Bạn cần gì?'
    return '🛍️ Cảm ơn bạn đã liên hệ GTShop! Để được hỗ trợ nhanh nhất, vui lòng gọi hotline 1800-1234 hoặc để lại tin nhắn, tôi sẽ trả lời sớm!'