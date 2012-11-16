import os, sys
import Image

SIZES = {1:20, 2:25, 3:30, 4:35, 5:40}

def save(img, path):
    img.save(path, 'PNG')

def scale(img, index, prefix):
    width = SIZES[index];
    height = int(round(width/67.0 * 81))
    size = (width, height)
    scaled = img.resize(size, Image.ANTIALIAS)
    path = '%s%s.png' % (prefix, index)
    save(scaled, path)

for infile in sys.argv[1:]:
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
    except IOError:
        print "cannot create thumbnail for '%s'" % infile
