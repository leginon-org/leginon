#!/usr/bin/env python

import sinedon
import mydata1 
import mydata2

### sinedon.cfg should have defined the connection parameters for mydata1 and
### mydata2
conf1 = sinedon.getConfig('mydata1')
print 'mydata1 config'
print conf1

conf2 = sinedon.getConfig('mydata2')
print 'mydata2 config'
print conf2

### Assuming that if I log in to one of those databases, I can access the
### other, I only need to connect to one of them.
db = sinedon.DB(**conf1)

def insertTest():
	# create instance of TData with a reference to an instance of AsdfData
	a = mydata1.AsdfData(aaaa='rr', bbbb='yy')
	t = mydata1.TData(ttt='asdfasdf', asdf=a)

	# create instance of OtherData with reference to instance of TData above
	s = mydata2.SomeData(name='third')
	o = mydata2.OtherData(name='jim', abc=s, t=t)

	# This single insert should recursively insert a new row into each 
	# of the four tables
	db.insert(o)

def queryTest():
	a = mydata1.AsdfData(aaaa='rr')
	t = mydata1.TData(ttt='asdfasdf', asdf=a)

	s = mydata2.SomeData(name='third')
	o = mydata2.OtherData(name='jim', abc=s, t=t)

	results = db.query(o)
	myresult = results[0]
	print 'QUERY RESULTS'
	print 'Other', myresult
	print 'Some', myresult['abc']
	print 'T', myresult['t']
	print 'Asdf', myresult['t']['asdf']

if __name__ == '__main__':
	insertTest()
	queryTest()
