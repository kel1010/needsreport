from django.core import cache
from functools import wraps

class Nil:
    pass

def cache_result(key_func, expires=600, expires_null=60, use='default'):
    def decorator(func):
        def inner(*args, **kwargs):
            key = 'NR_%s_%s_%s' % (func.__module__.replace('.', '_'), func.__name__, key_func(*args, **kwargs))
            try:
                c = cache.get_cache(use)
                result = c.get(key)
            except:
                logging.exception('Loading from cache %s failed. key: %s' % (use, key))
                result = None
                c = None
            if result==None:
                result = func(*args, **kwargs)
                if c:
                    try:
                        if result!=None:
                            c.set(key, result, expires)
                        else:
                            c.set(key, Nil, expires_null)
                    except:
                        logging.exception('Saving to cache %s failed. key: %s' % (use, key))
            elif result==Nil:
                result = None

            return result
        return wraps(func)(inner)

    return decorator
