from django.core.management.base import BaseCommand

from needsapp.mongodb import db
import csv

class Command(BaseCommand):
    def handle(self, *args, **options):
        with open(args[0], 'rb') as csvfile:
            for row in csv.reader(csvfile, delimiter=','):
                _type = row[0]
                keyword = row[1]
                obj = db.types.find_one({'type':_type})
                if not obj:
                    obj = {'type':_type, 'keywords':[keyword]}
                    db.types.save(obj)
                else:
                    if not keyword in obj['keywords']:
                        obj['keywords'].append(keyword)
                        db.types.save(obj)
