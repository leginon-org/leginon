import node
import data
import fftengine
import correlator
import peakfinder
import event
import time
import cPickle
import cameraimage
import camerafuncs
import gonmodel
import calibrationclient
import Numeric
import LinearAlgebra

False=0
True=1

class MatrixCalibrator(node.Node):
	def __init__(self, id, nodelocations, parameter, **kwargs):
		self.cam = camerafuncs.CameraFuncs(self)
		ffteng = fftengine.fftNumeric()
		#ffteng = fftengine.fftFFTW(planshapes=(), estimate=1)
		self.correlator = correlator.Correlator(ffteng)
		self.peakfinder = peakfinder.PeakFinder()

		if parameter not in ('image shift','stage position'):
			raise RuntimeError('parameter %s not supported' % (parameter,) )
		self.parameter = parameter

		self.axislist = ['x', 'y']
		self.settle = 2.0

		self.clearStateImages()

		node.Node.__init__(self, id, nodelocations, **kwargs)

		self.defineUserInterface()
		
	# calibrate needs to take a specific value
	def calibrate(self):
		self.clearStateImages()

		size = self.camerastate['size']
		bin = self.camerastate['binning']
		exp = self.camerastate['exposure time']
		camstate = {
			"dimension": {'x': size, 'y': size},
			"binning": {'x': bin, 'y': bin},
			"exposure time": exp
		}
		self.cam.autoOffset(camstate)

		camdata = data.EMData('camera', camstate)

		self.publish(event.LockEvent(self.ID()))
		self.publishRemote(camdata)

		baselist = []
		for i in range(self.navg):
			delta = i * 2e-5
			basex = self.base['x'] + delta
			basey = self.base['y'] + delta
			newbase = {'x':basex, 'y':basey}
			baselist.append(newbase)

		shifts = {}
		for axis in self.axislist:
			shifts[axis] = {'row': 0.0, 'col': 0.0}
			for base in baselist:
				print "axis =", axis
				basevalue = base[axis]

				print 'delta', self.delta
				newvalue = basevalue + self.delta
				print 'newvalue', newvalue

				state1 = self.makeState(basevalue, axis)
				state2 = self.makeState(newvalue, axis)
				print 'states', state1, state2
				shiftinfo = self.measureStateShift(state1, state2, axis)
				print 'shiftinfo', shiftinfo

				rowpix = shiftinfo['pixel shift']['row']
				colpix = shiftinfo['pixel shift']['col']
				totalpix = abs(rowpix + 1j * colpix)

				change = shiftinfo['parameter shift']
				perpix = change / totalpix
				print '**PERPIX', perpix

				rowpixelsper = rowpix / change
				colpixelsper = colpix / change
				shifts[axis]['row'] += rowpixelsper
				shifts[axis]['col'] += colpixelsper
				print 'shifts', shifts

			shifts[axis]['row'] /= self.navg
			shifts[axis]['col'] /= self.navg

		mag = self.getMagnification()
		self.publish(event.UnlockEvent(self.ID()))
		self.calclient.setCalibration(mag, shifts)

		print 'CALIBRATE DONE', shifts

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

	def measureStateShift(self, state1, state2, axis):
		'''measures the pixel shift between two states'''

		print 'acquiring state images'
		info1 = self.acquireStateImage(state1)
		info2 = self.acquireStateImage(state2)

		imagedata1 = info1['imagedata']
		imagedata2 = info2['imagedata']
		imagecontent1 = imagedata1.content
		imagecontent2 = imagedata2.content
		stats1 = info1['image stats']
		stats2 = info2['image stats']

		actual1 = imagecontent1['scope'][self.parameter][axis]
		actual2 = imagecontent2['scope'][self.parameter][axis]
		actual_shift = actual2 - actual1

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

		shiftinfo.update({'parameter shift': actual_shift, 'pixel shift': unbinned, 'peak value': peakvalue, 'shape':pcimage.shape, 'stats': (stats1, stats2)})
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

	def inRange(self, value, r):
		if (len(r) != 2) or (r[0] > r[1]):
			raise ValueError
		if (value >= r[0]) and (value <= r[1]):
			return True
		else:
			return False

	def correlate(self, image):
		# might also want to normalize with an autocorrelation of 
		# image 0, this might remove effects of poor gain normalization
		# but might also remove the correct peak for small shifts
		self.correlator.setImage(1, image)
		## phase correlation with new image
		try:
			pcimage = self.correlator.phaseCorrelate()
			#imagedata = data.ImageData(self.ID(), pcimage)
			#self.publish(imagedata, event.ImagePublishEvent)
		except correlator.MissingImageError:
			print 'missing image, no correlation'
			return

		## find peak in correlation image
		self.peakfinder.setImage(pcimage)
		peak = self.peakfinder.pixelPeak()
		peak = self.peakfinder.subpixelPeak()
		peak = self.peakfinder.getResults()
		print 'peak', peak
		peakvalue = peak['pixel peak value']
		print 'peak value', peakvalue
		## interpret as a shift
		shift = correlator.wrap_coord(peak['subpixel peak'], pcimage.shape)
		print 'shift', shift
		return {'shift': {'x': shift[1], 'y': shift[0]}, 'peak value': peakvalue}

	def defineUserInterface(self):
		nodespec = node.Node.defineUserInterface(self)

		#### parameters for user to set
		self.navg = 1
		self.delta = 5e-5

		self.camerastate = {'size': 1024, 'binning': 4, 'exposure time': 400}

		try:
			self.base = self.currentState()
		except:
			self.base = {'x': 0.0, 'y':0.0}
		####

		cspec = self.registerUIMethod(self.uiCalibrate, 'Calibrate', ())

		paramchoices = self.registerUIData('paramdata', 'array', default=('image shift', 'stage position'))

		argspec = (
		self.registerUIData('N Average', 'float', default=self.navg),
		self.registerUIData('Base', 'struct', default=self.base),
		self.registerUIData('Delta', 'float', default=self.delta),

		self.registerUIData('Camera State', 'struct', default=self.camerastate)
		)

		rspec = self.registerUIMethod(self.uiSetParameters, 'Set Parameters', argspec)

		self.validshift = self.registerUIData('Valid Shift', 'struct', permissions='rw')
		self.validshift.set(
			{
			'correlation': {'min': 20.0, 'max': 512.0},
			'calibration': {'min': 20.0, 'max': 512.0}
			}
		)

		self.registerUISpec('Matrix Calibrator', (cspec, rspec, self.validshift, nodespec))

	def uiCalibrate(self):
		self.calibrate()
		return ''

	def uiSetParameters(self, navg, base, delta, cs):
		self.navg = navg
		self.base = base
		self.delta = delta
		self.camerastate = cs
		return ''

	def makeState(self, value, axis):
		return {self.parameter: {axis: value}}

	def currentState(self):
		dat = self.researchByDataID(self.parameter)
		return dat.content[self.parameter]


class ImageShiftCalibrator(MatrixCalibrator):
	def __init__(self, id, nodelocations, **kwargs):
		param='image shift'
		self.calclient = calibrationclient.ImageShiftCalibrationClient(self)
		MatrixCalibrator.__init__(self, id, nodelocations, parameter=param, **kwargs)
		self.start()

class StageShiftCalibrator(MatrixCalibrator):
	def __init__(self, id, nodelocations, **kwargs):
		param='stage position'
		self.calclient = calibrationclient.StageCalibrationClient(self)
		MatrixCalibrator.__init__(self, id, nodelocations, parameter=param, **kwargs)
		self.start()
