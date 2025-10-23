from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Template filter para acessar itens de um dicionário por chave.
    Uso: {{ dict|get_item:key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)
