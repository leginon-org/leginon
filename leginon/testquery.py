#!/usr/bin/env python

import data
import dbdatakeeper


d = dbdatakeeper.DBDataKeeper(('fake',), 'fake')


## this is my root object
i = data.MyData()
i2 = data.MyData()
## these will be contained in MyData
mod = data.MyOtherData()
mod2 = data.MyOtherData()
mod2['stuff'] = 5
mod2['encore'] = 'une fois'


mod['stuff'] = 5
mod['encore'] = 'toto'
i['other'] = mod
i['id'] = ('me',2)
i2['other'] = mod
i2['id'] = ('me',3)

print 'INSERTING mod2:'
d.insert(mod2)

print 'INSERTING i:'
print i

d.insert(i)
print 'INSERTING i2:'
print i2
d.insert(i2)


# instance for query only
nmod = data.MyOtherData()
nmod['stuff'] = 5
nd = data.MyData()
nd['other'] = nmod


print 'QUERYING'
result = d.query(nd)
print 'RESULT'
print result

for e in result:
	print "other"
	print e['other']
	print "ID"
	print id(e['other'])
