from needsapp.contrib.mcache import cache_result

from django.template.defaultfilters import slugify

from Levenshtein import ratio as levratio

import urllib, urllib2
import json
import hashlib

BASE_URL='http://maps.googleapis.com/maps/api/geocode/json?sensor=false&address=%s'

GEOMETRY_TYPE = {"ROOTTOP": 4.0,
                 "RANGE_INTERPOLATED": 3.0,
                 "GEOMETRIC_CENTER": 1.0,
                 "APPROXIMATE": 0.0} 


@cache_result(lambda address: hashlib.md5(address).hexdigest(), expires=7*24*3600, use='location')
def google_geocode_fetch(address):
    url = BASE_URL % urllib.quote_plus(address)
    raw = urllib2.urlopen(url=url, timeout=30).read()
    return raw

def geocode(address):
    raw = google_geocode_fetch(address)
    data = json.loads(raw)
    best_score = 1.0
    best_result = None
    for result in data['results']:
        score = levratio(slugify(result['formatted_address']), slugify(address)) * 5.0 #levratio is between 0 and 1
        for addr in result['address_components']:
            if 'political' in addr['types']:
                score = score+0.2
        if 'partial_match' in result:
            score = score - 2.0
        score = score + GEOMETRY_TYPE.get(result['geometry']['location_type'], 0.0)
        if score > best_score:
            best_score = score
            best_result = result

    if best_result:
        return best_result['formatted_address'], best_result['geometry']['location'], best_score
    else:
        return None
