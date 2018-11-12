#!/usr/bin/env python
from pyscope import simccdcamera2
from pyami import mrc
import time
'''
This script is used to test camera acquisition time
'''
# Change the class initiated here to your camera
c = simccdcamera2.SimCCDCamera()
# Define test condition here
exposure_time_ms = 1000
binning = 2
repeats = 2

# No need to change below this line

dim0 = c.getDimension()
bin0 = c.getBinning()
bin1 = {'x':bin0['x']*binning,'y':bin0['y']*binning}
dim1 = {'x':dim0['x']/binning,'y':dim0['y']/binning}
c.setBinning(bin1)
c.setDimension(dim1)

for i in range(repeats):
	t0 = time.time()
	p = c.getImage()
	t1 = time.time()
	print 'image at binning %d took %.6f seconds' % (binning, t1 -t0)
	mrc.write(p,'test%d.mrc' % (i,))
	print 'image writing took %.6f seconds' % (t1 -t0)

c.setBinning(bin0)
c.setDimension(dim0)
raw_input('press return key to quit')

