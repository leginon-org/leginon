#!/usr/bin/env python

import data
import dbdatakeeper
import sys

print 'ORIGINAL'

###### create two instances of PresetImageData to insert ###########

scopedict = {'magnification': 1501, 'beam tilt': {'x':1.1,'y':2.2}}
cameradict = {'exposure time': 510, 'binning': {'x': 1, 'y':1}}
## PresetData
pdata = data.NewPresetData(('pdata',1))
pdata['name'] = 'hole3'
pdata['magnification'] = 1500
pdata['spot size'] = 4
pdata['beam shift'] = {'x': 5.5, 'y': 9.3}
pdata['exposure time'] = 500
pdata['binning'] = {'x': 8, 'y': 8}
## PresetImageData: contains PresetData
mydata = data.NewPresetImageData(('pidata', 1))
mydata['preset'] = pdata
mydata['scope'] = scopedict
mydata['camera'] = cameradict
print 'MYDATA'
print mydata

scopedict2 = {'magnification': 1801, 'beam tilt': {'x':5.1,'y':7.2}}
cameradict2 = {'exposure time': 810, 'binning': {'x': 1, 'y':1}}
## PresetData
pdata2 = data.NewPresetData(('pdata',2))
pdata2['name'] = 'square1'
pdata2['magnification'] = 1900
pdata2['spot size'] = 9
pdata2['beam shift'] = {'x': 1.331, 'y': 23.3}
pdata2['exposure time'] = 200
pdata2['binning'] = {'x': 22, 'y': 22}
## PresetImageData: contains PresetData
mydata2 = data.NewPresetImageData(('pidata', 2))
mydata2['preset'] = pdata2
mydata2['scope'] = scopedict2
mydata2['camera'] = cameradict2
print 'MYDATA2'
print mydata2

dbdk = dbdatakeeper.DBDataKeeper(('dbdk',1), 'testsession')

#dbdk.insert(mydata)
#dbdk.insert(mydata2)

#sys.exit()

##### create another instance of PresetImageData for the query  #####

cameradict3 = {'binning': {'x': 3, 'y':3}}
## PresetData
pdata3 = data.NewPresetData(('pdata',2))
pdata3['id'] = None
pdata3['magnification'] = 1900
## PresetImageData: contains PresetData
mydata3 = data.NewPresetImageData(('pidata', 2))
mydata3['id'] = None
mydata3['preset'] = pdata3
mydata3['camera'] = cameradict3
print 'MYDATA3'
print mydata3

mydata4 = dbdk.query(mydata3)
sys.exit()

## WAS LIKE THIS:
# mynode.research(data.NewPresetData, magnifcation=1900...)
# 	   mydata4 = dbdk.query(mydata3, )
#        in DBDataKeeper.query():
#              idata = data.NewPresetData(asdfd)

## SHOULD BE:
# mynode.research(data.NewPresetData, magnifcation=1900...)
#    newinstance = data.NewPresetData(magnifcation=1900...)
# mynode.research(partial)
# 


### THIS IS THE FINAL FORMAT FOR HOW NODE GETS DATA
# self.publish(mydata1, database=True)
# self.publish(mydata2, database=True)
# newdata = self.research(mydata3)


mylist = []
import random

### this is the function is never called directly
### It is called inside the replaceData() call below
def testfunc(mydata):
	print 'TESTFUNC'
	print mydata
	print ''

	mylist.append(mydata)

	### insert could be done here and retval should be last insert id
	####### INSERT HERE
	rnum = random.randrange(100000)

	retval = data.DataReference()
	retval['id'] = rnum
	retval['classname'] = mydata.__class__.__name__
	#print '    RETURNING',  retval
	return retval

# this executes testfunc on children of mydata
# and then on mydata itself.  Children are replaced with a DataReference
## this should be called either in dbdatakeeper or at a lower level
funcinfo = mydata.replaceData(testfunc)

print 'MYLIST'
print mylist
