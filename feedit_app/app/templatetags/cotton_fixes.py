from django import template

register = template.Library()


@register.tag
def endc(parser, token):
    """
    This is a dummy tag that does nothing.
    It's only purpose is to be registered so that the parser doesn't throw an error
    when it encounters the 'endc' tag used by django-cotton.
    """
    return template.Node()
