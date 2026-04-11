def cart_count(request):
    cart = request.session.get('cart', {})
    count = sum(item['quantity'] for item in cart.values())
    return {'cart_count': count}


def lang_list(request):
    """Danh sách ngôn ngữ cho dropdown navbar"""
    return {
        'lang_list': [
            ('vi',      '🇻🇳', 'Tiếng Việt'),
            ('en',      '🇺🇸', 'English'),
            ('zh-hans', '🇨🇳', '中文'),
            ('ja',      '🇯🇵', '日本語'),
            ('ru',      '🇷🇺', 'Русский'),
            ('km',      '🇰🇭', 'ភាសាខ្មែរ'),
        ]
    }