from django.core import cache

from functools import wraps

import hashlib
import logging

class Nil:
    pass

def _cache_result_key(func, key_func, *args, **kwargs):
    return 'N_%s_%s_%s' % (func.__module__.replace('.', '_'), func.__name__, key_func(*args, **kwargs))

def _do_cache(key, cache_defs, func, *args, **kwargs):
    
    if cache_defs:
        use = cache_defs[0].get('use')
        expires_none = cache_defs[0].get('expires_none', 300)
        expires = cache_defs[0].get('expires', 1800)

        try:
            c = cache.get_cache(use)
            result = c.get(key)
        except:
            logging.exception('Loading from cache %s failed. key: %s' % (use, key))
            result = None
            c = None            
    else:
        result = None

    if result==None:
        if cache_defs[1:]:
            result = _do_cache(key, cache_defs[1:], func, *args, **kwargs)
        else:
            result = func(*args, **kwargs)

        if c:
            try:
                if result is None:
                    c.set(key, Nil, expires_none)
                else:
                    c.set(key, result, expires)
            except:
                logging.exception('Saving to cache %s failed. key: %s' % (use, key))
    elif result==Nil:
        result = None

    return result

def mcache_result(key_func, cache_defs):    
    def decorator(func):
        def inner(*args, **kwargs):
            key = 'N_%s_%s_%s' % (func.__module__.replace('.', '_'), func.__name__, key_func(*args, **kwargs))
            return _do_cache(key, cache_defs[0], func, *args, **kwargs)
        return wraps(func)(inner)

    return decorator    

def cache_result(key_func, expires=1800, expires_none=300, use='default'):
    def decorator(func):
        def inner(*args, **kwargs):
            key = 'N_%s_%s_%s' % (func.__module__.replace('.', '_'), func.__name__, key_func(*args, **kwargs))
            cache_defs = [dict(expires=expires, expires_none=expires_none, use=use)]
            return _do_cache(key, cache_defs, func, *args, **kwargs)
        return wraps(func)(inner)

    return decorator

def cache_keygen(*args, **kwargs):
    key = unicode(args)+':'+unicode(kwargs)
    res = hashlib.md5(key).hexdigest()
    return res
