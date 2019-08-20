#!/usr/bin/env python
import time
from leginon import leginondata

def queryTest1():
	r = leginondata.AcquisitionImageData().query(results=1)
	if r:
		rdata = r[0]['target']
		return rdata
	else:
		print('Need one AcquisitionImageData from a target for this test.')

def query(wait_time):
	print('Testing query 2 times....')
	r1 = queryTest1()
	for i in range(2):
		print('%d' % (i+1,))
		d=r1['session']['comment']
		time.sleep(wait_time)
		r3=r1['session']['user']

seconds = float(raw_input('Enter wait time between tests in seconds: '))
d = "timeout test"
try:
	query(seconds)
	print("Success")
except Exception as e:
	print("Failed")
	print(e)
