#!/usr/bin/env python

import copy
import data
import strictdict


stupid = {
	'scope': {'intensity': 555, 'magnification': 4000},
	'camera': {'exposure time': 500},
	'preset': {'image shift': {'x': 234, 'y': 987}},
}

mylist = []
for i in range(5):
	newid = (str(i), i)
	#stupid2 = copy.deepcopy(stupid)
	stupid2 = {}
	stupid2['array row'] = i * 10
	stupid2['array column'] = i * 20
	itarget = data.ImageTargetData(newid, initializer=stupid2)
	mylist.append(itarget)
	print 'ITARGET'
	print itarget['array row'], itarget['array column']

xid = ('funstuff', 9)
listdata = data.ImageTargetListData(xid, targets=mylist)


listdatacopy = copy.deepcopy(listdata)
print 'CLASS', listdatacopy.__class__
print 'LISTDATACOPY', listdatacopy.keys()


targetlist = listdatacopy['targets']

for target in targetlist:
	print 'TARGET'
	print target['array row'], target['array column']
	print 'TARGETID', id(target)
