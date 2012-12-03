from needs.contrib.mcache import cache_result

from geopy import geocoders

import hashlib

@cache_result(lambda address: hashlib.md5(address).hexdigest(), expires=7200, use='location')
def geocode(address):
    geocoder = geocoders.Google()
    try:
        return geocoder.geocode(address, exactly_one=False)
    except:
        return None

