#!/usr/bin/env python
"""
Makes a small and simple stack for testing frame alignment program
It writes to local directory
"""
# parameters to change
size = (2048,2048)
drift = 3.0
number_of_frames = 20
feature_size = 2



import numpy
from pyami import mrc

zeros = numpy.zeros(size)
center_frame = number_of_frames / 2
start_center = (size[0]/2 - center_frame, size[1]/2 - center_frame)

for i in range(number_of_frames):
	print 'writing frame %d' % (i,)
	a = zeros * 1.0
	for p in range(feature_size):
		for q in range(feature_size):
			position = (int(round(start_center[0]+p+i*drift)),int(round(start_center[1]+q+i*drift)))
			a[position] = 5.0
	print position
	if i == 0:
			mrc.write(a,'frames.mrc')
	else:
		mrc.append(a,'frames.mrc')

	
