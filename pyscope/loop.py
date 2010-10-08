from pyscope import de12
import time
import numpy

d = de12.DE12()

d.setExposureTime(300)

t0 = time.time()
time_limit = 30 * 60
i = 0
print 'starting', t0
while True:
	i += 1
	print 'acquire', i
	try:
		image = d.getImage()
	except:
		raise
		print 'exception happened'
		image = None
	print 'image type', type(image)
	if not isinstance(image, numpy.ndarray):
		raw_input('*** not an array, press enter to continue')
	time.sleep(0.5)
	t1 = time.time()
	dt = t1 - t0
	print 'time', dt
	if dt > time_limit:
		break
raw_input('enter to quit')
