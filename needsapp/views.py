from django.http import HttpResponse
from django.template.defaultfilters import slugify
from django.views.decorators.cache import cache_page

from needsapp.mongodb import db, get_types_map, get_types
from needsapp.loc_query import geocode

from bson.code import Code

from twilio import twiml

import time
import json
import math
import copy
import base64
import uuid
import hashlib

CONTINENTS = [
    {'continent': 'Africa', 'latlng': [7.19, 21.10], 'zoom':3, 'abbrev': 'AF', 'countries': []},
    {'continent': 'Asia', 'latlng': [29.84, 89.30], 'zoom': 3, 'abbrev': 'AS', 'countries': []},
    {'continent': 'Australia', 'latlng': [-27.00, 133.0], 'zoom': 4, 'abbrev': 'OC', 'countries': []},
    {'continent': 'Europe', 'latlng': [48.69, 9.14], 'zoom': 4, 'abbrev': 'EU', 'countries': []},
    {'continent': 'North America', 'latlng': [46.07, -100.55], 'zoom': 3, 'abbrev': 'NA', 'countries': []},
    {'continent': 'South America', 'latlng': [-14.60, -57.66], 'zoom': 3, 'abbrev': 'SA', 'countries': []}
];

def uid_gen():
    return base64.urlsafe_b64encode(uuid.uuid4().bytes)[:-2]

def _find_type(request):
    slug = slugify(request.REQUEST.get('Body', ''))
    m = get_types_map()
    for _type in m.keys():
        if slug.find(_type.lower())>=0:
            return m[_type]

def _uid(request):
    return request.REQUEST['From']

def _new(request):

    r = twiml.Response()

    _type = _find_type(request)
    if not _type:
        r.sms('We only support %s needs. Please try again.' % ', '.join(get_types()))
        return HttpResponse(str(r))

    data = dict()

    data['body'] = request.REQUEST.get('Body', '')

    data['from_num'] = request.REQUEST.get('From', None)
    data['type'] = _type

    data['full'] = str(request.REQUEST)
    data['_id'] = _uid(request)
    data['created'] = time.time()

    data['country'] = request.REQUEST.get('FromCountry', None)

    uid = db.needs.save(data)

    if uid:
        if data['country']=='US':
            r.sms('Thanks for sending in your needs for %s. Where are you located? Please only enter city, state E.g. new york, ny' % _type)
        else:
            r.sms('Thanks for sending in your needs for %s. Where are you located? Please only enter city, provience, country E.g. istanbul, turkey' % _type)

    return HttpResponse(str(r))

def _confirm(request, data):
    location = request.REQUEST.get('Body', '')

    address = location
    res = geocode(address)

    r = twiml.Response()

    if res:
        place, loc = res[0]
        db.needs.update({'_id':_uid(request)}, {'$set': {'loc':loc, 'loc_place':place, 'loc_input':location}})

        count = db.needs.find({'loc_place':place}).count()

        if count>1:
            r.sms('There are %s requests for %s in your area.  Hopefully someone will take action.' % (count, data['type'].lower()))
        else:
            r.sms('You are the first person to request for %s in your area.  Thank you!' % data['type'].lower())
    else:
        r.sms('We do not understand where %s is.  Please try again.' % location)

    return HttpResponse(str(r))

def _too_old(data):
    t = data.get('created', 0)
    return not t or time.time()-t > 3600

def sms(request):
    uid = _uid(request)
    data = db.needs.find_one(dict(_id=uid))

    if not data or _too_old(data) or data.get('loc', None):
        return _new(request)
    else:
        return _confirm(request, data)

def _loc_defined(points):
    for point in points:
        if point==(None, None):
            return False

    return True

def _chart_data():
    # this map/reduce groups needs by month
    mapper = Code("""
        function() {
            var d = new Date(this.created*1000);
            var key = new Date(d.getUTCFullYear(), d.getUTCMonth(), 0, 0, 0, 0).getTime();
            emit(key, 1);
        }
    """)

    reducer = Code("""
        function(key, values) {
            var sum = 0;
            for (var i = 0; i < values.length; i++) {
                sum += values[i];
            }
            return sum;
        }
    """)

    data = []
    res = db.needs.map_reduce(mapper, reducer, 'tmp_%s' % uid_gen())
    for doc in res.find():
        data.append(dict(time=int(doc['_id']), sum=int(doc['value'])))

    res.drop()

    return data

@cache_page(7200)
def init_data(request):
    types = get_types()
    min_time_res = db.needs.find({'created':{'$exists': True}}).sort('created', 1).limit(1)
    if min_time_res.count()>0:
        min_time = min_time_res[0]['created']
    else:
        min_time = 1325376000

    continents = copy.deepcopy(CONTINENTS)
    for continent in continents:
        for country in db.countries.find({'continent':continent['abbrev']}).sort('country', 1):
            if 'latlng' not in country or country['latlng']==None:
                res = geocode(country['country'])
                if res:
                    place, latlng = res[0]
                    country['latlng'] = latlng
                else:
                    print 'No geocode for: %s' % country['country']
                    country['latlng'] = None
                db.countries.save(country)

            if 'area' in country and country['area']>0:
                pop_log = int(math.log(abs(country['area']), 12))
            else:
                pop_log = 4

            continent['countries'].append({'country': country['country'], 'latlng': country['latlng'], 'zoom': 10-pop_log})

    chart_data = _chart_data()
    params = dict(types=types, min_time=min_time, continents=continents, chart_data=chart_data)
    return HttpResponse(json.dumps(params), content_type='application/json')    

def map_data(request):
    req = json.loads(request.raw_post_data)
    start = int(req.get('start', 0))
    end = int(req.get('end', time.time()))
    _types = req.get('types', None)
    condition = {'loc':{'$exists': True}, 'created':{'$lte': end, '$gte': start}}
    if _types:
        condition['type'] = {'$in': _types}

    # this map/reduce groups needs by location
    mapper = Code("""
        function() {
            var key = this.type+this.loc_place;
            emit(key, {sum:1, type:this.type, loc:this.loc, loc_place:this.loc_place});
        }
    """)

    reducer = Code("""
        function(key, values) {
            var sum = 0;
            for (var i = 0; i < values.length; i++) {
                sum += values[i].sum;
            }
            return {sum: sum, type: values[0].type, loc: values[0].loc, loc_place: values[0].loc_place}
        }
    """)

    # this map/reduce picks the highest needs for a location
    mapper2 = Code("""
        function() {
            var key = this.value.loc_place;
            emit(this.value.loc_place, this.value);
        }
    """)
    
    reducer2 = Code("""
        function(key, values) {
            var max = values[0];
            for (var i=1; i<values.length; ++i) {
                if (max.sum < values[i].sum) {
                    max = values[i];
                } 
            }
            return max;
        }
    """)

    tmp = db.needs.map_reduce(mapper, reducer, 'tmp_%s' % uid_gen(), query=condition)
    res = tmp.map_reduce(mapper2, reducer2, 'tmp_%s' % uid_gen())
    locs = []
    for doc in res.find():
        locs.append(doc['value'])

    data = []
    for loc in locs:
        value = int(math.log(loc['sum'], 10))+1
        if value>5:
            value=5
        loc['value'] = value
        loc['type'] = loc['type'].title()
        data.append(loc)

    tmp.drop()
    res.drop()

    return HttpResponse(json.dumps(dict(types=get_types(), data=data)), content_type='application/json')

def loc_data(request):
    req = json.loads(request.raw_post_data)
    loc_place = req['loc_place']
    start = int(req.get('start', 0))
    end = int(req.get('end', time.time()))

    mapper = Code("""
        function() {
            emit(this.type, 1);
        }
    """)

    reducer = Code("""
        function(key, values) {
            var sum = 0;
            for (var i = 0; i < values.length; i++) {
                sum += values[i];
            }
            return sum;
        }
    """)

    condition = {'loc_place':loc_place, 'created':{'$lte': end, '$gte': start}}
    res = db.needs.map_reduce(mapper, reducer, 'tmp_%s' % uid_gen(), query=condition)

    data = []
    for doc in res.find():
        data.append(dict(type=doc['_id'], sum=int(doc['value'])))

    res.drop()
    data.sort(lambda a,b: b['sum']-a['sum'])

    return HttpResponse(json.dumps(data), content_type='application/json')

def latest_needs(request):
    since = request.REQUEST.get('since', None)
    if since:
        condition = {'created': {'$gt': int(since)}}
        sort = ('created', 1)
    else:
        condition = {}
        sort = ('created', -1)
    res = db.needs.find(condition).sort([sort]).limit(30)
    data = []
    for doc in res:
        data.append(dict(created=doc['created'], loc_place=doc['loc_place'], loc=doc['loc'], type=doc['type']))

    if not since:
        data.reverse()

    return HttpResponse(json.dumps(data), content_type='application/json')
