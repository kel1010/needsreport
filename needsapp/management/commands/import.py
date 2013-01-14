from django.core.management.base import BaseCommand

from needsapp.mongodb import db
from needsapp import sms
from needsapp.contrib import uid_gen
from needsapp.loc_query import geocode

import csv


class Command(BaseCommand):
    def handle(self, *args, **options):
        first_row = True
        with open(args[0], 'rb') as csvfile:
            for row in csv.reader(csvfile, delimiter=','):
                if row[0] and not first_row:
                    location = row[1]+","+row[0]
                    needs = row[2:5]
                    for need in needs:
                        if need:
                            data = dict()
                            data['from_num'] = '1111'
                            _type = sms._find_type(needs[0])
                            if _type:
                                data['type'] = sms._find_type(needs[0])
                            data['_id'] = uid_gen()
                            data['words'] = map(lambda w: w.lower().strip(), need.split(' '))
                            data['loc_input'] = location
                            res = geocode(data['loc_input'])

                            if res:
                                place, loc, score = res
                                data.update({'loc':loc, 'loc_place':place, 'loc_score':score})                            

                            data['created'] = 1333425600
                            
                            db['needs'].save(data)
                            
                first_row = False