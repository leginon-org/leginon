#!/usr/bin/env python

import data
import dbdatakeeper


d = dbdatakeeper.DBDataKeeper(('fake',), 'fake')


## this is my root object
i = data.MyData()
## these will be contained in MyData
mod = data.MyOtherData()

mod['stuff'] = 5
i['other'] = mod

print 'INSERTING i:'
print i

d.insert(i)

print 'QUERYING'
result = d.query(i)
print 'RESULT'
print result
