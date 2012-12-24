from django.core.management.base import BaseCommand

import os, logging
import Image

SIZES = {1:20, 2:25, 3:30, 4:35, 5:40}

def save(img, path):
    img.save(path, 'PNG')

def scale(img, index, prefix):
    width = SIZES[index];
    height = int(round(width*81.0/67.0))
    size = (width, height)
    scaled = img.resize(size, Image.ANTIALIAS)
    path = '%s%s.png' % (prefix, index)
    save(scaled, path)

def scale_cluster(img, index, prefix):
    width = SIZES[index]+20;
    height = width
    size = (width, height)
    scaled = img.resize(size, Image.ANTIALIAS)
    path = '%s_cluster%s.png' % (prefix, index)
    
    save(scaled, path)

class Command(BaseCommand):
    def handle(self, *args, **options):
        for infile in args:
            prefix = os.path.splitext(infile)[0][1:]
            try:
                full = Image.open(infile)
                crop = (35, 32, 35+75, 32+81)
                cropped = full.crop(crop)

                scale(cropped.copy(), 1, prefix)
                scale(cropped.copy(), 2, prefix)
                scale(cropped.copy(), 3, prefix)
                scale(cropped.copy(), 4, prefix)
                scale(cropped.copy(), 5, prefix)

                scale_cluster(full.copy(), 1, prefix)
                scale_cluster(full.copy(), 2, prefix)
                scale_cluster(full.copy(), 3, prefix)
                scale_cluster(full.copy(), 4, prefix)
                scale_cluster(full.copy(), 5, prefix)

            except IOError, e:
                logging.exception(e)
                print "cannot create thumbnail for '%s'" % infile
