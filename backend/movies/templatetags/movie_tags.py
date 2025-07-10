from django import template

register = template.Library()

@register.filter
def get_genres(movie):
    """Get genres from movie object whether it's a Django model or dictionary."""
    if hasattr(movie, 'genres'):
        genres = movie.genres
        # Check if it's a related manager by checking for 'all' method
        if hasattr(genres, 'all') and callable(genres.all):
            return genres.all()
        else:
            return genres
    return []

@register.filter
def is_iterable(obj):
    """Check if object is iterable (but not string)."""
    try:
        iter(obj)
        return not isinstance(obj, (str, bytes))
    except TypeError:
        return False
