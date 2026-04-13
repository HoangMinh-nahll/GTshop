from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

@csrf_exempt
@require_POST
def apply_voucher(request):
    # TODO: implement logic áp dụng voucher
    return JsonResponse({'error': 'Chức năng đang phát triển'}, status=501)

@csrf_exempt
@require_POST
def remove_voucher(request):
    # TODO: implement logic xóa voucher
    return JsonResponse({'error': 'Chức năng đang phát triển'}, status=501)