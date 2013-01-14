from django.http import HttpResponse
from django.views.decorators.cache import cache_page
from django.conf import settings
from django.shortcuts import render_to_response

from needsapp.mongodb import db, get_types
from needsapp.loc_query import geocode
from needsapp.contrib.mcache import cache_result
from needsapp.contrib import uid_gen

from bson.code import Code

import time
import json
import math
import copy

CONTINENTS = [
    {'continent': 'Africa', 'latlng': [7.19, 21.10], 'zoom':3, 'abbrev': 'AF', 'countries': []},
    {'continent': 'Asia', 'latlng': [29.84, 89.30], 'zoom': 3, 'abbrev': 'AS', 'countries': []},
    {'continent': 'Australia', 'latlng': [-27.00, 133.0], 'zoom': 4, 'abbrev': 'OC', 'countries': []},
    {'continent': 'Europe', 'latlng': [48.69, 9.14], 'zoom': 4, 'abbrev': 'EU', 'countries': []},
    {'continent': 'North America', 'latlng': [46.07, -100.55], 'zoom': 3, 'abbrev': 'NA', 'countries': []},
    {'continent': 'South America', 'latlng': [-14.60, -57.66], 'zoom': 3, 'abbrev': 'SA', 'countries': []}
];

def _loc_defined(points):
    for point in points:
        if point==(None, None):
            return False

    return True

@cache_result(lambda: '', expires=4*3600)
def _chart_data():
    # this map/reduce groups needs by month
    mapper = Code("""
        function() {
            var d = new Date(this.created*1000);
            var key = new Date(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate(), 0, 0, 0).getTime();
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
    res = db['needs'].map_reduce(mapper, reducer, 'tmp_%s' % uid_gen())
    for doc in res.find():
        data.append([int(doc['_id']), int(doc['value'])])

    res.drop()

    return data

@cache_page(180)
def init_data(request):
    types = get_types()
    min_time_res = db['needs'].find({'created':{'$exists': True}}).sort('created', 1).limit(1)
    if min_time_res.count()>0:
        min_time = min_time_res[0]['created'] - 7*24*3600
    else:
        min_time = 1325376000

    continents = copy.deepcopy(CONTINENTS)
    for continent in continents:
        for country in db['countries'].find({'continent':continent['abbrev']}).sort('country', 1):
            if 'latlng' not in country or country['latlng']==None:
                res = geocode(country['country'])
                if res:
                    place, latlng, score = res
                    country['latlng'] = latlng
                else:
                    print 'No geocode for: %s' % country['country']
                    country['latlng'] = None
                db['countries'].save(country)

            if 'area' in country and country['area']>0:
                pop_log = int(math.log(abs(country['area']), 12))
            else:
                pop_log = 4

            continent['countries'].append({'country': country['country'], 'latlng': country['latlng'], 'zoom': 10-pop_log})

    chart_data = copy.deepcopy(_chart_data())
    chart_data.append([int(time.time()*1000), 0])
    params = dict(types=types, min_time=min_time, continents=continents, chart_data=chart_data)
    return HttpResponse(json.dumps(params), content_type='application/json')    

def map_data(request):
    req = json.loads(request.raw_post_data)
    start = int(req.get('start', 0))
    end = int(req.get('end', time.time()))
    words = set(req.get('words', '').split(','))
    if '' in words:
        words.remove('')

    if abs(time.time()-end) < 24*3600:
        end=time.time()+3600
        
    if abs(time.time()-start) < 24*3600:
        start = start - 24*3600;        

    _types = req.get('types', None)
    condition = {'loc':{'$exists': True}, 'created':{'$lte': end, '$gte': start}}
    if words:
        condition['words'] = {'$in': map(lambda word: word.lower().strip(), words)}
    elif _types:
        condition['type'] = {'$in': _types}
    else:
        condition['type'] = {'$exists': 1}

    print condition

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

    tmp = db['needs'].map_reduce(mapper, reducer, 'tmp_%s' % uid_gen(), query=condition)
    res = tmp.map_reduce(mapper2, reducer2, 'tmp_%s' % uid_gen())
    locs = []
    for doc in res.find():
        locs.append(doc['value'])

    data = {}
    for loc in locs:
        value = int(math.log(loc['sum'], 10))+1
        if value>5:
            value=5
        loc['value'] = value

        if 'type' in loc and loc['type']:
            _type = loc['type'].title()
        elif words:
            _type = 'Other'
            loc['type'] = 'Other'

        if _type not in data:
            data[_type] = list()
        data[_type].append(loc)

    tmp.drop()
    res.drop()

    return HttpResponse(json.dumps(dict(types=get_types(), data=data)), content_type='application/json')

def loc_data(request):
    req = json.loads(request.raw_post_data)
    loc_place = req['loc_place']
    start = int(req.get('start', 0))
    end = int(req.get('end', time.time()))
    words = set(req.get('words', '').split(','))    
    if '' in words:
        words.remove('')

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
    if words:
        condition['words'] = {'$in': map(lambda word: word.lower().strip(), words)}
    else:
        condition['type'] = {'$exists': 1}

    res = db['needs'].map_reduce(mapper, reducer, 'tmp_%s' % uid_gen(), query=condition)

    data = []
    for doc in res.find():
        if not doc['_id']:
            if words:
                data.append(dict(type='Other', sum=int(doc['value'])))
        else:
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
    res = db['needs'].find(condition).sort([sort]).limit(30)
    data = []
    for doc in res:
        data.append(dict(created=doc['created'], loc_place=doc['loc_place'], loc=doc['loc'], type=doc['type']))

    if not since:
        data.reverse()

    return HttpResponse(json.dumps(data), content_type='application/json')

def index(request):
    return render_to_response("index.html", dict(STATIC_URL=settings.STATIC_URL, SMS_NUMBER=settings.SMS_NUMBER, TEST_SITE=settings.TEST_SITE, GA_ID=settings.GA_ID))
