from django import template

register = template.Library()


@register.simple_tag
def half_star_range():
    """
    Returns [(0.5, 'half'), (1.0, 'full'), (1.5, 'half'), ..., (5.0, 'full')]
    so we can assign proper mask class for 0.5 vs full star.
    """
    steps = []
    for i in range(1, 11):
        val = i / 2
        mask = "mask-half-1" if val % 1 != 0 else "mask-half-2"
        steps.append((val, mask))
    return steps
