#!/usr/bin/env python
"""
Makes a small and simple stack for testing frame alignment program
It writes to local directory
"""
import numpy
from pyami import mrc
size = (512,512)
zeros = numpy.zeros(size)
drift = 10

for i in range(7):
	print 'writing frame %d' % (i,)
	a = zeros * 1.0
	a[(size[0]/2+i*drift,size[1]/2+i*drift)] = 1.0
	a[(size[0]/2+1+i*drift,size[1]/2+i*drift)] = 1.0
	a[(size[0]/2+i*drift,size[1]/2+1+i*drift)] = 1.0
	a[(size[0]/2+1+i*drift,size[1]/2+1+i*drift)] = 1.0
	if i == 0:
		mrc.write(a,'frames.mrc')
	else:
		mrc.append(a,'frames.mrc')

	
