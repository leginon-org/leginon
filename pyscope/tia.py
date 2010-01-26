import ccdcamera
import comarray
from win32com.client import Dispatch
import pythoncom
import numpy

class TIA(ccdcamera.CCDCamera):
	name = 'TIA'

	def __init__(self):
		self.unsupported = [
			'getPixelSize',
			'getInserted', 'setInserted',]
		ccdcamera.CCDCamera.__init__(self)
        	pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)
		self.im = None
		self.imdisp = None
		self.tianame = 'pyscope'
		self.setupname = self.tianame + ' Setup'
		self.imagedispname = self.tianame + ' Image Display'
		self.imagename = self.tianame + ' Image'
		self._connectToESVision()
		self.initSettings()

	def initSettings(self):
		self.dimension = self.getCameraSize()
		self.binning = {'x':1, 'y':1}
		self.offset = {'x':0, 'y':0}
		self.exposure = 500
		self.exposuretype = 'normal'
	def setDimension(self, value):
		self.dimension = value
	def getDimension(self):
		return self.dimension
	def setBinning(self, value):
		self.binning = value
	def getBinning(self):
		return self.binning
	def setOffset(self, value):
		self.offset = value
	def getOffset(self):
		return self.offset
	def setExposureTime(self, value):
		self.exposure = value
	def getExposureTime(self):
		return self.exposure

	def _connectToESVision(self):
		'''
		Connects to the ESVision COM server
		'''
		self.esv = Dispatch('ESVision.Application')
		self.acqman = self.esv.AcquisitionManager()
		self.ccd = self.esv.CcdServer()

		## scan mode to spot so CCD can be setup
		#self.esv.ScanningServer().ScanMode = 0

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
		try:
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
		except:
			print 'could not set', kwargs

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
		if self.imdisp is None:
			self.imdisp = self.dispwin.AddDisplay(self.imagedispname, 0, 0, 0, 1)
		## create image in image display
		cal = self.esv.Calibration2D(0,0,1,1,0,0)
		sizex = self.ccd.PixelReadoutRange.SizeX
		sizey = self.ccd.PixelReadoutRange.SizeY
		if self.im is not None:
			self.imdisp.DeleteObject(self.im)
		self.im = self.imdisp.AddImage(self.imagename, sizex, sizey, cal)
		self.acqman.LinkSignal('CCD', self.im)

	def getExposureTypes(self):
		return ['normal', 'dark']

	def getExposureType(self):
		return self.exposuretype

	def setExposureType(self, value):
		if value not in ['normal', 'dark']:
			raise ValueError('invalid exposure type')
		self.exposuretype = value

	def getPixelSize(self):
		## this is the Eagle 4k camera
		return {'x': 1.5e-5, 'y': 1.5e-5}

	def getCameraSize(self):
		rangex = self.ccd.GetTotalPixelReadoutRange().SizeX
		rangey = self.ccd.GetTotalPixelReadoutRange().SizeY
		camsize = {'x':rangex, 'y':rangey}
		return camsize

	def finalizeSetup(self):
		# final bin
		bin = self.binning['x']

		# final range
		unbindim = {'x':self.dimension['x']*bin, 'y':self.dimension['y']*bin}
		off = self.offset
		range = self.getConfig('range')
		range.StartX = off['x']
		range.StartY = off['y']
		range.EndX = off['x'] + unbindim['x']
		range.EndY = off['y'] + unbindim['y']

		# final exposure time
		if self.exposuretype == 'dark':
			exposure = self.ccd.GetIntegrationTimeRange().Start
		else:
			exposure = self.exposure/1000.0

		# send it to camera
		self.setConfig(binning=bin, range=range, exposure=exposure)

	def _getImage(self):
		'''
		Acquire an image using the setup for this ESVision client.
		'''
		try:
			self.selectSetup()
			self.finalizeSetup()
			self.acqman.Acquire()
			arr = comarray.prop(self.im.Data, 'Array')
			arr = numpy.flipud(arr)
		except Exception, e:
			print e
			arr = None
		return arr

	def getRetractable(self):
		retractable = bool(self.ccd.IsCameraRetractable())
		return retractable

	'''
	def getInserted(self):
		if self.getRetractable():
			return self.ccd.CameraInserted
		else:
			return True

	def setInserted(self, value):
		if self.getRetractable():
			self.ccd.CameraInserted = value
		else:
			raise NotImplementedError('getInserted')
	'''

	def getEnergyFiltered(self):
		return False
