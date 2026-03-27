from django import template

register = template.Library()

@register.filter
def currency(value):
    try:
        value = int(value)
        return f"{value:,}".replace(",", ".") + "₫"
    except (ValueError, TypeError):
        return ""