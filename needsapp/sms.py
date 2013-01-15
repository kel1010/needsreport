from django.template.defaultfilters import slugify
from django.http import HttpResponse

from needsapp.mongodb import db, get_types_map
from needsapp.contrib import validate_twilio
from needsapp.loc_query import geocode
from needsapp.contrib import uid_gen

from Levenshtein import ratio as levratio

from twilio import twiml

import time

EXCLUDE_WORDS = ['', 'needs', 'need', 'want', 'i', 'we', 'us', 'request', 'requests', 'the', 'and', 'or', 'in', 'to', 'have', 'has', 'for', 'my']

def _find_type(text):
    slug = slugify(text)
    m = get_types_map()
    res = None
    max_score = 0.9
    for word in slug.split('-'):
        for _type in m.keys():
            score = levratio(word, _type)
            if score>max_score:
                res = m[_type]
                max_score = score

    return res

def _number(request):
    slug = slugify(request.REQUEST['From'])
    return ''.join(slug.split('-'))

def _new(request):

    r = twiml.Response()

    _type = _find_type(request.REQUEST.get('Body', ''))

    data = dict()

    if _type:
        data['type'] = _type

    data['body'] = request.REQUEST.get('Body', '')

    number = _number(request)

    data['from_num'] =  number
    data['session'] = number

    data['full'] = str(request.REQUEST)
    data['_id'] = uid_gen()
    data['created'] = time.time()

    data['country'] = request.REQUEST.get('FromCountry', None)

    words = set(map(lambda w: w.lower().strip(), request.REQUEST.get('Body', '').split(' ')))
    for exclude_word in EXCLUDE_WORDS:
        if exclude_word in words:
            words.remove(exclude_word)

    data['words'] = list(words)

    uid = db['needs'].save(data)

    if uid:
        if data['country']=='US':
            if _type:
                r.sms('Thanks for sending in your needs for %s. Where are you located? Please only enter city, state E.g. elmhurst, ny' % _type)
            else:
                r.sms('Thanks for sending in your need. Where are you located? Please only enter city, state E.g. elmhurst, ny')
        else:
            r.sms('Thanks for sending in your needs for %s. Where are you located? Please only enter city, provience E.g. Montreal, Quebec' % _type)

    return HttpResponse(str(r))

def _confirm(request, data):
    location = request.REQUEST.get('Body', '')

    address = location
    res = geocode(address.strip().lower(), request.REQUEST.get('FromCountry', '').lower())

    r = twiml.Response()

    if res:
        place, loc, score = res
        db['needs'].update({'_id':data['_id']}, {'$set': {'loc':loc, 'loc_place':place, 'loc_input':location, 'loc_score':score, 'session': None}})

        if data.get('type', None):
            count = db['needs'].find({'loc_place':place, 'type':data['type']}).count()
    
            if count>1:
                r.sms('There are %s needs for %s in your area.  Hopefully someone will take action.' % (count, data['type'].lower()))
            else:
                r.sms('You are the first person to report the need for %s in your area.  Thank you!' % data['type'].lower())
        else:
            r.sms('Thank you!  Your need is registered')
    else:
        r.sms('We do not understand where %s is.  Please try again.' % location)

    return HttpResponse(str(r))

def _too_old(data):
    t = data.get('created', 0)
    return not t or time.time()-t > 3600

@validate_twilio
def handle_sms(request):
    _session = _number(request)
    data = db['needs'].find_one(dict(session=_session))

    if not data or _too_old(data) or data.get('loc', None):
        return _new(request)
    else:
        return _confirm(request, data)
    