from pymongo import Connection, GEO2D

connection = Connection('localhost', 27017)
db = connection.needs_db

needs_coll = db.needs
needs_coll.ensure_index([('loc', GEO2D)])
needs_coll.ensure_index('loc_place')
