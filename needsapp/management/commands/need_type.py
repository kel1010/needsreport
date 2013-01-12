from django.core.management.base import BaseCommand
from needsapp import sms

class Command(BaseCommand):

    def handle(self, *args, **options):
        print sms._find_type(args[0])
