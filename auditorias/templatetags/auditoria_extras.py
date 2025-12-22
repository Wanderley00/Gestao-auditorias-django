# auditorias/templatetags/auditoria_extras.py

from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Permite acessar itens de um dicionário usando uma variável no template.
    Ex: {{ meu_dicionario|get_item:minha_chave }}
    """
    return dictionary.get(key)


@register.filter
def rem_page_param(query_dict):
    """
    Remove o parâmetro 'page' de um QueryDict (request.GET)
    para ser usado na paginação.
    Ex: {{ request.GET.urlencode|rem_page_param }}
    """
    # Cria uma cópia mutável do QueryDict
    query_dict = query_dict.copy()

    # Remove a chave 'page' se ela existir
    if 'page' in query_dict:
        del query_dict['page']

    # Retorna a string de query codificada sem o 'page'
    return query_dict.urlencode()


@register.filter
def abreviar_status(texto_status):
    """
    Abrevia os status longos para exibição na tabela.
    """
    if not texto_status:
        return ""

    mapeamento = {
        'Aguardando Validação': 'Ag. Validação',
        'Aguardando Aprovação': 'Ag. Aprovação',
        'Validação de Eficácia': 'Val. Eficácia',
        'Em Implementação': 'Implementação',  # Opcional: remove o "Em"
        'Desvio Solucionado': 'Solucionado',
        'Não Conformidade': 'NC',
        'Oportunidade de Melhoria': 'OM'
    }

    # Retorna o valor abreviado se existir no mapa, senão retorna o original
    return mapeamento.get(texto_status, texto_status)
