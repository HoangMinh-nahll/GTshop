from django import template

register = template.Library()


@register.filter
def currency(value):
    """Định dạng tiền VND: 10000 → 10.000đ"""
    try:
        v = int(value)
        return f"{v:,}đ".replace(',', '.')
    except (TypeError, ValueError):
        return str(value)


@register.filter
def get_item(dictionary, key):
    """Lấy giá trị từ dict bằng key: {{ dict|get_item:key }}"""
    try:
        return dictionary.get(int(key))
    except (TypeError, ValueError, AttributeError):
        return dictionary.get(key)