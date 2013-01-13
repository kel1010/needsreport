from django.conf import settings
from pymongo import Connection, GEO2D

from needsapp.contrib.mcache import cache_result

connection = Connection(settings.MONGO_HOST)
db = connection[settings.MONGO_DB]

db.needs = db['needs']
db.countries = db['countries']
db.types = db['types']

db.needs.ensure_index([('loc', GEO2D)])
db.needs.ensure_index('loc_place')
db.needs.ensure_index('created')
db.needs.ensure_index('words')

db.countries.ensure_index('country')
db.countries.ensure_index('continent')

@cache_result(lambda: '', expires=3600*24)
def get_types_map():
    res = dict()
    for obj in db.types.find():
        for keyword in obj['keywords']:
            res[keyword] = obj['type']
            
    return res

@cache_result(lambda: '', expires=3600*24)
def get_types():
    m = get_types_map()
    types = list(set(m.values()))
    return sorted(types)
