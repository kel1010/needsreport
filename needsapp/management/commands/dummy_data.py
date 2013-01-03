from django.core.management.base import BaseCommand

from needsapp.mongodb import db, get_types
from needsapp.loc_query import geocode

import random 
import time
import uuid

START_TIME = 978325200

class Command(BaseCommand):

    def __init__(self):
        self.current_time = time.time()
        self.countries = list()
        for country in db.countries.find():
            self.countries.append(country)

    def random_time(self):
        return int(random.random()*(self.current_time-START_TIME)+START_TIME)
    
    def random_country(self):
        country = random.choice(self.countries)
        if country.get('capital') and country.get('country'):
            return country
        else:
            return self.random_country()
    
    def handle(self, *args, **options):
        for num in range(0, 1000):
            data = dict()
    
            data['from_num'] = num
            data['type'] = random.choice(get_types())
            data['created'] = self.random_time()
            data['_id'] = uuid.uuid4().hex
            
            country = self.random_country()
            
            data['country'] = country.get('iso', None)

            data['loc_input'] = '%s, %s' % (country['capital'], country['country'])
    
            res = geocode(data['loc_input'])

            if res:
                place, loc, score = res
                data.update({'loc':loc, 'loc_place':place, 'loc_score':score})

            db.needs.insert(data)        
