#!/usr/bin/env python

import csv
import json
import sys

f = open( sys.argv[1], 'r' )
reader = csv.reader(f, delimiter='\t')
title = reader.next()
res = list()
for row in reader:
    data = dict()
    for index, value in enumerate(row):
        try:
            if title[index]:
                field = title[index].replace(' ', '_').lower()
                if value.strip():
                    if field=='area':
                        data[field] = float(value)
                    elif field=='population':
                        data[field] = int(value)
                    else:
                        data[field] = value.strip()
        except:
            pass
    res.append(data)
out = json.dumps(res)
print out

