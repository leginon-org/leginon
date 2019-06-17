from pyscope import tia
from pyami import mrc
import time
'''
This script is used to test camera acquisition time
'''
# Change the class initiated here to your camera
c = tia.TIA_Ceta()
# Define test condition here
exposure_time_ms = (500.0,1000.0,2000.0)
for t in exposure_time_ms:
	c.setExposureTime(t)
	c.getImage()
	for j in range(5):
		t1 = time.time()
		c.acqman.Acquire()
		print t,t1
raw_input('press return key to quit')

