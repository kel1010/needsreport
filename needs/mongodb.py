from pymongo import Connection, GEO2D

from needs.contrib.mcache import cache_result

connection = Connection('localhost', 27017)
db = connection.needs_db

db.needs.ensure_index([('loc', GEO2D)])
db.needs.ensure_index('loc_place')
db.needs.ensure_index('created')

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
