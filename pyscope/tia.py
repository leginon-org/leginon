from ccdcamera import CCDCamera
import NumpySafeArray
from win32com.client import Dispatch

class TIA(CCDCamera):
	name = 'TIA'

	def __init__(self):
		self.tianame = 'pyScope'
		self.setupname = self.tianame + ' Setup'
		self.imagedispname = self.tianame + ' Image Display'
		self.imagename = self.tianame + ' Image'
		self._connectToESVision()

	def _connectToESVision(self):
		'''
		Connects to the ESVision COM server
		'''
		self.esv = Dispatch('ESVision.Application')
		self.acqman = self.esv.AcquisitionManager()
		self.ccd = self.esv.CcdServer()

		## scan mode to spot so CCD can be setup
		self.esv.ScanningServer().ScanMode = 0

		## new display window
		disp = self.esv.FindDisplayWindow(self.tianame)
		if disp is not None:
			self.esv.CloseDisplayWindow(self.tianame)
		self.dispwin = self.esv.AddDisplayWindow()
		self.dispwin.Name = self.tianame
		if self.acqman.DoesSetupExist(self.setupname):
			self.acqman.DeleteSetup(self.setupname)
		self.acqman.AddSetup(self.setupname)

	def selectSetup(self):
		self.esv.ActivateDisplayWindow(self.tianame)
		self.acqman.SelectSetup(self.setupname)
		self.ccd.AcquireMode = 1
		self.ccd.SeriesSize = 1

	def setConfig(self, **kwargs):
		'''
range is the sequence:  xmin, ymin, xmax, ymax
binning is an integer binning factor
exposure is the exposure time in seconds
		'''
		self.selectSetup()
		if 'range' in kwargs:
			range = kwargs['range']
			self.ccd.PixelReadoutRange = range
		if 'binning' in kwargs:
			binning = kwargs['binning']
			self.ccd.Binning = binning
		if 'exposure' in kwargs:
			exposure = kwargs['exposure']
			self.ccd.IntegrationTime = exposure
		self.updateImageDisplay()

	def getConfig(self, param):
		self.selectSetup()
		if param == 'range':
			return self.ccd.PixelReadoutRange
		elif param == 'binning':
			return self.ccd.Binning
		elif param == 'exposure':
			return self.ccd.IntegrationTime

	def updateImageDisplay(self):
		'''
Call this method following any reconfiguration of acquisition
parameters.  This will update the image display and prepare for
acquisition.
		'''
		## add image display
		imdisp = self.dispwin.AddDisplay(self.imagedispname, 0, 0, 0, 1)
		## create image in image display
		cal = self.esv.Calibration2D(0,0,1,1,0,0)
		sizex = self.ccd.PixelReadoutRange.SizeX
		sizey = self.ccd.PixelReadoutRange.SizeY
		self.im = imdisp.AddImage(self.imagename, sizex, sizey, cal)
		self.acqman.LinkSignal('CCD', self.im)

	def getBinning(self):
		binfactor = self.getConfig('binning')
		return {'x':binfactor, 'y':binfactor}

	def setBinning(self, value):
		binfactor = value['x']
		self.configureCCD(binning=binfactor)

	def getOffset(self):
		range = self.getConfig('range')
		offset = {'x':range.StartX, 'y':range.StartY}
		return offset

	def setOffset(self, value):
		range = getConfig('range')
		range.StartX = value['x']
		range.StartY = value['y']
		self.setConfig(range=range)

	def getUnbinnedDimension(self):
		range = self.getConfig('range')
		dimx = range.SizeX
		dimy = range.SizeY
		return {'x':dimx, 'y':dimy}

	def setUnbinnedDimension(self, value):
		range = self.getConfig('range')
		range.SizeX = value['x']
		range.SizeY = value['y']
		self.setConfig(range=range)

	def getDimension(self):
		unbindim = self.getUnbinnedDimension()
		bin = self.getBinning()
		dim = {'x':unbindim['x']/bin['x'], 'y':unbindim['y']/bin['y']}
		return dim

	def setDimension(self, value):
		bin = self.getBinning()
		unbindim = {'x':bin['x']*value['x'], 'y':bin['y']*value['y']}
		self.setUnbinnedDimension(unbindim)

	def getExposureTime(self):
		seconds = self.getConfig('exposure')
		ms = int(1000 * seconds)
		return ms

	def setExposureTime(self, value):
		seconds = value/1000.0
		self.setConfig(exposure=seconds)

	def getExposureTypes(self):
		raise NotImplementedError

	def getExposureType(self):
		raise NotImplementedError

	def setExposureType(self, value):
		raise NotImplementedError

	def getPixelSize(self):
		raise NotImplementedError

	def getCameraSize(self):
		range = self.ccd.GetTotalPixelReadoutRange()
		camsize = {'x':range.SizeX, 'y':range.SizeY}
		return camsize

	def _getImage(self):
		'''
		Acquire an image using the setup for this ESVision client.
		This will not work unless you have previously called
		configureCCD.

		This (unfortunately) returns a Python tuple of tuples from
		the COM SafeArray.
		'''
		self.selectSetup()
		self.acqman.Acquire()
		arr = NumpySafeArray.prop(self.im.Data, 'Array')
		return arr

	def getRetractable(self):
		retractable = bool(self.ccd.IsCameraRetractable())
		return retractable

	def getInserted(self):
		if self.getRetractable():
			return self.ccd.CameraInserted
		else:
			raise NotImplementedError('getInserted')

	def setInserted(self, value):
		if self.getRetractable():
			self.ccd.CameraInserted = value
		else:
			raise NotImplementedError('getInserted')

	def getEnergyFiltered(self):
		return False
