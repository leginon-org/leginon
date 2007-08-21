#!/usr/bin/env python

import mydata1 
import mydata2

def insertTest():
	# create instance of TData with a reference to an instance of AsdfData
	a = mydata1.AsdfData(aaaa='rr', bbbb='yy')
	t = mydata1.TData(ttt='asdfasdf', asdf=a)

	# create instance of OtherData with reference to instance of TData above
	s = mydata2.SomeData(name='third')
	o = mydata2.OtherData(name='jim', abc=s, t=t)

	# This single insert should recursively insert a new row into each 
	# of the four tables
	o.insert()

def queryTest():
	a = mydata1.AsdfData(aaaa='rr')
	t = mydata1.TData(ttt='asdfasdf', asdf=a)

	s = mydata2.SomeData(name='third')
	o = mydata2.OtherData(name='jim', abc=s, t=t)

	results = o.query()
	myresult = results[0]
	print 'QUERY RESULTS'
	print 'Other', myresult
	print 'Some', myresult['abc']
	print 'T', myresult['t']
	print 'Asdf', myresult['t']['asdf']

if __name__ == '__main__':
	insertTest()
	queryTest()
