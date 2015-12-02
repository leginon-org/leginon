import comtypes.client
import ccdcamera
import numpy
import time
import falconframe
## create a single connection to TIA COM object.
## Muliple calls to get_tiaccd will return the same connection.
## Store the handle in the com module, which is safer than in
## this module due to multiple imports.
class TIAConnection(object):
	esv = None
	acqman = None
	ccd = None

connection = TIAConnection()
comtypes.client.tiaccd = connection
def get_tiaccd():
	global connection
	if connection.esv is None:
		try:
			comtypes.CoInitializeEx(comtypes.COINIT_MULTITHREADED)
		except:
			comtypes.CoInitialize()
		connection.esv = comtypes.client.CreateObject('ESVision.Application')
		connection.acqman = connection.esv.AcquisitionManager()
		connection.ccd = connection.esv.CcdServer()
	return connection

class TIA(ccdcamera.CCDCamera):
	name = 'TIA'
	camera_name = 'tia'

	def __init__(self):
		self.unsupported = [
			'getPixelSize',
			'getInserted', 'setInserted',]
		ccdcamera.CCDCamera.__init__(self)
		self.im = None
		self.imdisp = None
		# Each camera needs its own display name
		self.tianame = 'pyscope-%s' % (self.camera_name)
		self.setupname = self.tianame + ' Setup'
		self.imagedispname = self.tianame + ' Image Display'
		self.imagename = self.tianame + ' Image'
		# set save_frames here because super is used in TIA_Falcon first
		# still not sure why it matters Issue #2874
		self.save_frames = False
		self._connectToESVision()
		self.initSettings()

	def __getattr__(self, name):
		# When asked for self.camera, instead return self._camera, but only
		# after setting the current camera id
		if name == 'ccd':
			if self.camera_name is not None:
				self._ccd.Camera = self.camera_name
			return self._ccd
		else:
			return ccdcamera.CCDCamera.__getattribute__(self, name)

	def initSettings(self):
		self.dimension = self._getCameraSize()
		self.binning = {'x':1, 'y':1}
		self.offset = {'x':0, 'y':0}
		self.exposure = 500.0
		self.exposuretype = 'normal'

	def getCameraModelName(self):
		return self.camera_name

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

	def setExposureTime(self, ms):
		self.exposure = float(ms)

	def getExposureTime(self):
		# milliseconds
		return float(self.exposure)

	def _connectToESVision(self):
		'''
		Connects to the ESVision COM server
		'''
		connection = get_tiaccd()
		self.esv = connection.esv
		self.acqman = connection.acqman
		self._ccd = connection.ccd

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

	def _getCameraSize(self):
		rangex = self.ccd.GetTotalPixelReadoutRange.SizeX
		rangey = self.ccd.GetTotalPixelReadoutRange.SizeY
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
			exposure = self.ccd.GetIntegrationTimeRange.Start
		else:
			exposure = self.exposure/1000.0

		# send it to camera
		self.setConfig(binning=bin, range=range, exposure=exposure)


	def custom_setup(self):
		'''
		Camrea specific setup
		'''
		pass

	def getImage(self):
		try:
			## scan mode to spot so CCD can be setup on scope with STEM
			self.esv.ScanningServer().ScanMode = 0
		except:
			## scope withou STEM mode would fail this call
			pass
		# The following is copied from ccdcamera.CCDCamera since
		# super (or self.as_super as used in de.py) does not work in proxy call
		if self.readoutcallback:
			name = str(time.time())
			self.registerCallback(name, self.readoutcallback)
			self.backgroundReadout(name)
		else:
			return self._getImage()

	def _getImage(self):
		'''
		Acquire an image using the setup for this ESVision client.
		'''
		try:
			self.selectSetup()
			self.custom_setup()
			self.finalizeSetup()
		except:
			raise RunTimeError('Error setting camera acquisition parameters')

		t0 = time.time()

		try:
			self.acqman.Acquire()
			t1 = time.time()
			self.exposure_timestamp = (t1 + t0) / 2.0
			arr = self.im.Data.Array
		except:
			raise RunTimeError('Camera Acquisition Error in getting array')

		try:
			arr.shape = (self.dimension['y'],self.dimension['x'])
			arr = numpy.flipud(arr)
		except AttributeError, e:
			print 'comtypes did not return an numpy 2D array, but %s' % (type(arr))
		except Exception, e:
			print e
			arr = None
		return arr

	def getRetractable(self):
		retractable = bool(self.ccd.IsCameraRetractable)
		return retractable

	def getInserted(self):
		if self.getRetractable():
			return self.ccd.CameraInserted
		else:
			return True

	def setInserted(self, value):
		# return if already at this insertion state
		if not self.getRetractable() or not (value ^ self.getInserted()):
			return
		if value:
			sleeptime = 5
		else:
			sleeptime = 1
		self.ccd.CameraInserted = value
		time.sleep(sleeptime)

	def getEnergyFiltered(self):
		return False

class TIA_Eagle(TIA):
	name = 'Eagle'
	camera_name = 'BM-Eagle'
# Note:  only known to work with 4kx4k Eagle.
# Multiplier, "M" determined by acquiring a series of dark/bright pairs
# at different binning values.  Nothing else should change
# during the series (constant beam intensity, exposure time...)
# For each pair, subtract dark from bright, calc the mean value.
# The value "M" is determined for each binning.  M=1.0 for binning=1.
# For binning = x:
# M = binning^2 * mean_of_bin1_image / mean_of_binx_image
	def getBinnedMultiplier(self):
		binning = self.binning['x']
		if binning == 1:
			return 1.0
		elif binning == 2:
			return 2.9
		elif binning == 4:
			return 6.6
		elif binning == 8:
			return 7.8

class TIA_Falcon(TIA):
	name = 'Falcon'
	camera_name = 'BM-Falcon'
	binning_limits = [1,2,4]

	def __init__(self):
		super(TIA_Falcon,self).__init__()
		self.frameconfig = falconframe.FalconFrameConfigXmlMaker(False)
		self.movie_exposure = 500.0
		self.start_frame_number = 1
		self.end_frame_number = 7
		self.equal_distr_frame_number = 0

	def getPixelSize(self):
		return {'x': 1.4e-5, 'y': 1.4e-5}

	def setInserted(self, value):
		super(TIA_Falcon,self).setInserted(value)
		if value == False:
			# extra pause for Orius insert since Orius might think
			# it is already inserted
			time.sleep(4)

	#==========Frame Saving========================
	def getSaveRawFrames(self):
		'''Save or Discard'''
		return self.save_frames
	def setSaveRawFrames(self, value):
		'''True: save frames, False: discard frames'''
		self.save_frames = bool(value)

	def getNumberOfFrames(self):
		if self.save_frames:
			return self.frameconfig.getNumberOfFrameBins()
		else:
			return 1

	def calculateMovieExposure(self):
		'''
		Movie Exposure is the exposure time to set to ConfigXmlMaker in ms
		'''
		self.movie_exposure = self.end_frame_number * self.frameconfig.getBaseFrameTime() * 1000.0
		self.frameconfig.setExposureTime(self.movie_exposure / 1000.0)

	def getReadoutDelay(self):
		'''
		Integrated image readout delay is always base_frame_time.
		There is no way to change it.
		'''
		return None

	def validateUseFramesMax(self,value):
		'''
		Return end frame number valid for the integrated image exposure time.
		'''
		if not self.save_frames:
			return 1
		# find number of frames the exposure time will give as the maximun
		self.frameconfig.setExposureTime(float(self.exposure) / 1000)
		max_input_frame_value = self.frameconfig.getNumberOfAvailableFrames() - 1 
		return min(max_input_frame_value, max(value,1))

	def setUseFrames(self, frames):
		'''
		UseFrames gui for Falcon is a tuple of base_frames that defines
		the frames used in the movie.  For simplicity in input, we only
		use the min number as the movie delay and max number as the highest
		frame number to include.
		'''
		if frames:
			if len(frames) > 1:
				self.frameconfig.setFrameReadoutDelay(min(frames))
			else:
				self.frameconfig.setFrameReadoutDelay(1)
			self.end_frame_number = self.validateUseFramesMax(max(frames))
		else:
			# default movie to start at frame 1 ( i.e., not include roll-in)
			self.frameconfig.setFrameReadoutDelay(1)
			# use impossible large number to get back value for exposure time
			self.end_frame_number = self.validateUseFramesMax(1000)
		self.start_frame_number = self.frameconfig.getFrameReadoutDelay()
		# set equally distributed frames starting frame number
		if len(frames) >2:
			framelist = list(frames)
			framelist.sort()
			self.equal_distr_frame_number = framelist[1]
		else:
			self.equal_distr_frame_number = 0
		self.frameconfig.setEquallyDistributedStartFrame(self.equal_distr_frame_number)

		self.calculateMovieExposure()

	def getUseFrames(self):
		'''
		returns tuple for "use frames" gui.  Set it to None if
		not saving frames to avoid changing future useframes value
		'''
		if self.save_frames:
			if self.equal_distr_frame_number > self.start_frame_number:
				return (self.start_frame_number,self.equal_distr_frame_number,self.end_frame_number)
			else:
				return (self.start_frame_number,self.end_frame_number)

	def setFrameTime(self,ms):
		'''
		OutputFrameTime is not detrmined by the user
		'''
		pass

	def getFrameTime(self):
		'''
		Output frame time is the average time of all frame bins.
		'''
		ms = self.movie_exposure / self.getNumberOfFrames()
		return ms

	def getPreviousRawFramesName(self):
		return self.frameconfig.getFrameDirName()

	def custom_setup(self):
		self.calculateMovieExposure()
		movie_exposure_second = self.movie_exposure/1000.0
		if self.save_frames:
			self.frameconfig.makeRealConfigFromExposureTime(movie_exposure_second,self.equal_distr_frame_number,self.start_frame_number)
		else:
			try:
				self.frameconfig.makeDummyConfig(movie_exposure_second)
			except:
				# In case falconframe.py is not set up right
				pass

	def getSystemGainDarkCorrected(self):
		return True

	def getFrameFlip(self):
		'''
		Frame Flip is defined as up-down flip
		'''
		return False

	def getFrameRotate(self):
		'''
		Frame Rotate direction is defined as x to -y rotation applied after up-down flip
		'''
		return 3

class TIA_Orius(TIA):
	name = 'Orius'
	camera_name = 'BM-Orius'

class TIA_Ceta(TIA):
	name = 'Ceta'
	camera_name = 'BM-Ceta'

	def getSystemGainDarkCorrected(self):
		return True

	def getPixelSize(self):
		return {'x': 1.4e-5, 'y': 1.4e-5}

