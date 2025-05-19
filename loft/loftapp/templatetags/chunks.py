from django import template

register = template.Library()
@register.filter(name='chunks')
def chunks(list_data, chunk_size):
    chunk = []
    for item in list_data:
        chunk.append(item)
        if len(chunk) == chunk_size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk  # Yield remaining items