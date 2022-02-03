from pyami import mrc
from pyscope import instrumenttype
import time
'''
This script is used to test camera acquisition time
'''
# This tests the first camera found in instruments.cfg
search_for = 'Camera'
c = instrumenttype.getInstrumentTypeInstance(search_for)
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
	try:
		print('returned image shape', p.shape)
	except AttributeError as e:
		print('Error: Returned image not an array.')
		if type(p) == type(()):
			print('----Did you replace safearray.py in comtypes installation as instructed?')
		break
	print 'image at binning %d took %.6f seconds' % (binning, t1 -t0)
	mrc.write(p,'test%d.mrc' % (i,))
	print 'image writing took %.6f seconds' % (t1 -t0)

c.setBinning(bin0)
c.setDimension(dim0)
raw_input('press return key to quit')

