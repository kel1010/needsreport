from django.core.management.base import BaseCommand

from needsapp.loc_query import geocode

class Command(BaseCommand):
    def handle(self, *args, **options):
        print geocode(args[0])