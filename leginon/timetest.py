#!/usr/bin/env python

import time
import sys

#### Choose either numarray or numpy

################ numarray ##################
if True:
	import numarray
	import numarray.random_array as rand
	int32 = numarray.Int32
	float32 = numarray.Float32
	num = numarray
################ numpy ##################
else:
	import numpy
	rand = numpy.random
	int32 = numpy.int32
	float32 = numpy.float32
	num = numpy

def timefunc(n, func, args):
	t0 = time.time()
	for i in range(n):
		t00 = time.time()
		func(*args)
		t11 = time.time()
		print '        %7.3f' % (t11-t00,)
	t1 = time.time()
	total = t1 - t0
	percall = total / n
	print ''
	print '%7.3f %7.3f' % (total, percall)

def randomData(mb):
	'Generate mb megabytes of random data'
	## will create array with 4 byte integers
	n = 1024 * 1024 * mb / 4
	a = rand.randint(-2147483648, 2147483648, n)
	a = num.asarray(a, int32)
	return a

def saveData(a, filename):
	f = open(filename, 'w')
	a.tofile(f)
	f.close()

def saveRandomData(mb, filename):
	a = randomData(mb)
	saveData(a, filename)

def timeRandomData(n, mb):
	timefunc(n, randomData, (mb,))

def timeSaveData(n, mb, filename):
	a = randomData(mb)
	timefunc(n, saveData, (a, filename))

def timeSaveRandomData(n, mb, filename):
	timefunc(n, saveRandomData, (mb, filename))

def correct(n):
	b = rand.random((4096,4096))
	c = rand.random((4096,4096))
	for i in range(n):
		print 'random array', i
		a = rand.random((4096,4096))
		print 'astype'
		a = a.astype(float32)
		print a.type()
		print 'correct'
		print time.time()
		d = (a - b) * c
		print time.time()
		print 'done'

def despike(n):
	for i in range(n):
		print 'random array', i
		a = numarray.random_array.random((4096,4096))
		print 'astype'
		a = a.astype(numarray.Float32)
		print a.type()
		print 'correct'
		print time.time()
		imagefun.despike(a)
		print time.time()
		print 'done'

if __name__ == '__main__':
	filename = sys.argv[1]
	n = int(sys.argv[2])
	mb = int(sys.argv[3])
	timeSaveData(n, mb, filename)
