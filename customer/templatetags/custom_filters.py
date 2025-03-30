from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Returns the value of the given key in a dictionary, or None if key is missing."""
    if isinstance(dictionary, dict):  # Ensure it's a dictionary before accessing `.get()`
        return dictionary.get(key)
    return None  # Return None instead of raising an error
