import node, event, data
import fftengine
import correlator
import peakfinder
import time
import camerafuncs
import calibrationclient

False=0
True=1

class Calibrator(node.Node):
	'''
	Calibrator base class
	Contains basic functions useful for doing calibrations
	'''
	def __init__(self, id, nodelocations, **kwargs):
		self.cam = camerafuncs.CameraFuncs(self)
		ffteng = fftengine.fftNumeric()
		#ffteng = fftengine.fftFFTW(planshapes=(), estimate=1)
		self.correlator = correlator.Correlator(ffteng)
		self.peakfinder = peakfinder.PeakFinder()

		self.settle = 2.0
		self.clearStateImages()

		node.Node.__init__(self, id, nodelocations, **kwargs)

	def getMagnification(self):
		magdata = self.researchByDataID('magnification')
		return magdata.content['magnification']

	def clearStateImages(self):
		self.images = []

	def acquireStateImage(self, state):
		## acquire image at this state
		newemdata = data.EMData('scope', state)
		self.publish(event.LockEvent(self.ID()))
		self.publishRemote(newemdata)
		print 'state settling time %s' % (self.settle,)
		time.sleep(self.settle)

		actual_state = self.currentState()
		imagedata = self.cam.acquireCameraImageData(camstate=None, correction=0)
		self.publish(imagedata, event.CameraImagePublishEvent)

		## should find image stats to help determine validity of image
		## in correlations
		image_stats = None

		info = {'requested state': state, 'imagedata': imagedata, 'image stats': image_stats}
		self.images.append(info)
		return info

	def measureStateShift(self, state1, state2):
		'''
		Measures the pixel shift between two states
		 Returned dict has these keys:
		    'actual states': tuple with the actual scope states
		    'pixel shift': the resulting pixel shift, 'row', and 'col'
		    'peak value': cross correlation peak value
		    'shape': shape of acquired images
		    'stats': statistics of two images acquired (not implemented)
		'''

		print 'acquiring state images'
		info1 = self.acquireStateImage(state1)
		info2 = self.acquireStateImage(state2)

		imagedata1 = info1['imagedata']
		imagedata2 = info2['imagedata']
		imagecontent1 = imagedata1.content
		imagecontent2 = imagedata2.content
		stats1 = info1['image stats']
		stats2 = info2['image stats']

		actual1 = imagecontent1['scope']
		actual2 = imagecontent2['scope']
		actual = (actual1, actual2)

		shiftinfo = {}

		numimage1 = imagecontent1['image']
		numimage2 = imagecontent2['image']

		self.correlator.insertImage(numimage1)

		## autocorrelation
		self.correlator.insertImage(numimage1)
		acimage = self.correlator.phaseCorrelate()
		acimagedata = data.PhaseCorrelationImageData(self.ID(), acimage, imagedata1.id, imagedata1.id)
		#self.publish(acimagedata, event.PhaseCorrelationImagePublishEvent)

		## phase correlation
		self.correlator.insertImage(numimage2)
		print 'correlation'
		pcimage = self.correlator.phaseCorrelate()

		## subtract autocorrelation
		pcimage -= acimage

		pcimagedata = data.PhaseCorrelationImageData(self.ID(), pcimage, imagedata1.id, imagedata2.id)
		#self.publish(pcimagedata, event.PhaseCorrelationImagePublishEvent)

		## peak finding
		print 'peak finding'
		self.peakfinder.setImage(pcimage)
		self.peakfinder.subpixelPeak()
		peak = self.peakfinder.getResults()
		peakvalue = peak['subpixel peak value']
		shift = correlator.wrap_coord(peak['subpixel peak'], pcimage.shape)

		## need unbinned result
		binx = imagecontent1['camera']['binning']['x']
		biny = imagecontent1['camera']['binning']['y']
		unbinned = {'row':shift[0] * biny, 'col': shift[1] * binx}

		shiftinfo.update({'actual states': actual, 'pixel shift': unbinned, 'peak value': peakvalue, 'shape':pcimage.shape, 'stats': (stats1, stats2)})
		return shiftinfo


	### some of this should be put directly in Correlator 
	### maybe have phaseCorrelate check validity of its result
	def validateShift(self, shiftinfo):
		'''
		Calculate the validity of an image correlation
		Reasons for rejection:
		  - image shift too large to measure with given image size
		        results in poor correlation
		  - pixel shift too small to use as calibration data
		  	results in good correlation, but reject anyway
		'''
		shift = shiftinfo['pixel shift']
		## Jim is proud of coming up with this ingenious method
		## of calculating a hypotenuse without importing math.
		## It's definietly too late to be working on a Friday.
		totalshift = abs(shift[0] * 1j + shift[1])
		print 'totalshift', totalshift
		peakvalue = shiftinfo['peak value']
		shape = shiftinfo['shape']
		stats = shiftinfo['stats']

		validshiftdict = self.validshift.get()
		print 'validshiftdict', validshiftdict

		## for now I am ignoring percent, only using pixel
		validshift = validshiftdict['calibration']
		print 'validshift', validshift

		## check if shift too small
		if (totalshift < validshift['min']):
			return 'small'
		elif (totalshift > validshift['max']):
			return 'big'
		else:
			return 'good'

	def currentState(self):
		dat = self.researchByDataID('scope')
		return dat.content
