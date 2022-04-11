from django import template


register = template.Library()


@register.filter
def get_value(dict, key):
    return dict.get(key)
