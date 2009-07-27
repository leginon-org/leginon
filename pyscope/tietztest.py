from pyScope import tietz
import time

# one of these classes should work
tietzclasses = [
	tietz.TietzPXL,
	tietz.TietzPVCam,
	tietz.TietzSCX,
	tietz.TietzFC415,
]

successful = []
for cls in tietzclasses:
	print 'Killing any CAMC4 procs'
	tietz.killCamcProcs()

	print 'Trying to initialize: %s' % (cls,)
	myccd = None
	tries = 2
	for i in range(1,tries+1):
		try:
			myccd = cls()
			print '   Succeed on try %d of %d' % (i, tries)
			break
		except:
			print '   Failed to initialize on try %d of %d' % (i,tries)

	if myccd is None:
		continue

	print '   Waiting 3 seconds...'
	time.sleep(3)

	if not tietz.listCamcProcs():
		continue

	print '   Trying to get camera configuration...'
	try:
		dim = myccd.getDimension()
		print '   Dimension:', dim
		bin = myccd.getBinning()
		print '   Binning:', bin
		off = myccd.getOffset()
		print '   Offset:', off
	except:
		print '   Failed to get configuration'
		continue

	print '   Trying to acquire 0.5 sec exposure (large image may take several seconds)...'
	try:
		myccd.setExposureTime(500)
		image = myccd.getImage()
	except:
		print '   Failed to acquire image'

	print '   SUCCESS!!!'
	successful.append(cls)
	print '   deleting class instance...'
	del myccd
	print '   Waiting 3 seconds...'
	time.sleep(3)
	print ''

print ''
print '********** Test complete. **********'
print 'These classes were successful.  Use one in instruments.cfg:'
for cls in successful:
	print '   ', cls.__name__
if not successful:
	print '   None'
else:
	print 'Example for instruments.cfg:'
	print '  [My Camera]'
	print '  class: tietz.%s' % (successful[0].__name__,)
	print ''
raw_input('Hit enter to quit')
