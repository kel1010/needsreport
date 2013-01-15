from django.core.management.base import BaseCommand

from needsapp.loc_query import geocode

class Command(BaseCommand):
    def handle(self, *args, **options):
        if len(args)==2:
            print geocode(args[0], args[1])
        else:
            print geocode(args[0])
