#import comtypes.client
import ccdcamera
import time
import simscripting
import falconframe
from pyscope import moduleconfig

SIMULATION = False
class FEIAdvScriptingConnection(object):
	instr = None
	csa = None
	cameras = []

if SIMULATION:
	# There is problem starting numpy in FEI 2.9 software as FEI version of python2.7 becomes the default.
	import numpy
	import simscripting
	connection = simscripting.Connection()
else:
	import comtypes
	import comtypes.client
	connection = FEIAdvScriptingConnection()

READOUT_FULL = 0
READOUT_HALF = 1
READOUT_QUARTER = 2

configs = moduleconfig.getConfigured('fei.cfg')
## create a single connection to TIA COM object.
## Muliple calls to get_feiadv will return the same connection.
## Store the handle in the com module, which is safer than in
## this module due to multiple imports.
def get_feiadv():
	global connection
	if connection.instr is None:
		try:
			comtypes.CoInitializeEx(comtypes.COINIT_MULTITHREADED)
		except:
			comtypes.CoInitialize()
		connection.instr = comtypes.client.CreateObject('TEMAdvancedScripting.AdvancedInstrument.1')
		connection.acq = connection.instr.Acquisitions
		connection.csa = connection.acq.CameraSingleAcquisition
		connection.cameras = connection.csa.SupportedCameras
	return connection

def get_feiadv_sim():
	connection.instr = connection.Instrument
	connection.acq = connection.instr.Acquisitions
	connection.csa = connection.acq.CameraSingleAcquisition
	connection.cameras = connection.csa.SupportedCameras
	return connection

class FeiCam(ccdcamera.CCDCamera):
	name = 'FEICAM'
	camera_name = 'FEI_CAM'

	def __init__(self):
		self.unsupported = []
		ccdcamera.CCDCamera.__init__(self)
		self.save_frames = False
		self._connectToFEIAdvScripting()
		self.setReadoutLimits()
		self.initSettings()

	def __getattr__(self, name):
		# When asked for self.camera, instead return self._camera, but only
		# after setting the current camera id
		if name == 'camera':
			if self.camera_name is not None:
				self._ccd = self.getCamera()
			return self._ccd
		else:
			return ccdcamera.CCDCamera.__getattribute__(self, name)

	def getFeiConfig(self,optionname,itemname=None):
		if optionname not in configs.keys():
			return None
		if itemname is None:
			return configs[optionname]
		else:
			if itemname not in configs[optionname]:
				return None
			return configs[optionname][itemname]

	def initSettings(self):
		self.dimension = self.getCameraSize()
		self.binning = {'x':1, 'y':1}
		self.offset = {'x':0, 'y':0}
		self.exposure = 500.0
		self.exposuretype = 'normal'

	def setReadoutLimits(self):
		readout_dicts = {READOUT_FULL:1,READOUT_HALF:2,READOUT_QUARTER:4}
		self.sorted_readout_keys = (READOUT_QUARTER, READOUT_HALF, READOUT_FULL)
		size = self.getCameraSize()
		self.limit_dim = {}
		self.limit_off = {}
		for k in self.sorted_readout_keys:
			self.limit_dim[k] = {'x': size['x']/readout_dicts[k], 'y': size['y']/readout_dicts[k]}
			self.limit_off[k] = {'x': int((size['x']-self.limit_dim[k]['x'])/2.0), 'y':int((size['y']-self.limit_dim[k]['y'])/2.0)}
		self.readout_offset = {'x':0,'y':0}

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

	def getCamera(self):
		for c in self.csa.SupportedCameras:
			if c.Name == self.camera_name:
				return c
		return None

	def _connectToFEIAdvScripting(self):
		'''
		Connects to the ESVision COM server
		'''
		if SIMULATION:
			connection = get_feiadv_sim()
		else:
			connection = get_feiadv()
		self.instr = connection.instr
		self.csa = connection.csa
		# TODO: setCamera
		this_camera = self.getCamera()
		if this_camera is None:
			raise ValueError('%s not found' % self.camera_name)
		# set to this camera
		self.csa.Camera = this_camera
		# set attributes
		self.camera = this_camera
		self.camera_settings = self.csa.CameraSettings

	def setConfig(self, **kwargs):
		'''
range is the sequence:  xmin, ymin, xmax, ymax
binning is an integer binning factor
exposure is the exposure time in seconds
		'''
		try:
			if 'readout' in kwargs:
				readout = kwargs['readout']
				self.camera_settings.ReadoutArea = readout
			if 'binning' in kwargs:
				binning = kwargs['binning']
				# assum x and y binnings are the same
				self.camera_settings.Binning.Width = binning['x']
				self.camera_settings.Binning.Height = binning['y']
			if 'exposure' in kwargs:
				exposure = kwargs['exposure']
				self.camera_settings.ExposureTime = exposure
		except:
			raise
			print 'could not set', kwargs

	def getConfig(self, param):
		if param == 'readout':
			return self.camera_settings.ReadoutArea
		elif param == 'binning':
			return {'x':self.camera_settings.Binning.Width,'y':self.camera_settings.Binning.Height}
		elif param == 'exposure':
			return self.camera_settings.ExposureTime

	def getExposureTypes(self):
		return ['normal', 'dark']

	def getExposureType(self):
		return self.exposuretype

	def setExposureType(self, value):
		if value not in ['normal', 'dark']:
			raise ValueError('invalid exposure type')
		self.exposuretype = value

	def getPixelSize(self):
		pixelsize = self.camera.PixelSize #in meters
		return {'x': pixelsize, 'y': pixelsize}

	def getReadoutAreaKey(self,unbindim, off):
		for k in self.sorted_readout_keys:
			limit_off = self.limit_off[k]
			limit_dim = self.limit_dim[k]
			if (off['x'] >= limit_off['x']
				and off['y'] >= limit_off['y']
				and	off['x']+unbindim['x'] <= limit_dim['x']+limit_off['x']
				and off['y']+unbindim['y'] <= limit_dim['y']+limit_off['y']):
				return k
		raise ValueError('Does not fit any defined readout area')

	def getReadoutOffset(self, key, full_off):
		limit_off = self.limit_off[key]
		return {'x':full_off['x']-limit_off['x'],'y':full_off['x']-limit_off['y']}

	def finalizeSetup(self):
		# final bin
		binning = self.binning

		# final range
		unbindim = {'x':self.dimension['x']*binning['x'], 'y':self.dimension['y']*binning['y']}
		off = self.offset
		readout_key = self.getReadoutAreaKey(unbindim, off)
		exposure = self.exposure/1000.0

		# send it to camera
		self.setConfig(readout=readout_key, exposure=exposure)


	def custom_setup(self):
		'''
		Camrea specific setup
		'''
		pass

	def getImage(self):
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
		Acquire an image using the setup for this client.
		'''
		try:
			self.finalizeSetup()
			self.custom_setup()
		except:
			raise
			raise RuntimeError('Error setting camera acquisition parameters')

		t0 = time.time()

		try:
			self.im = self.csa.Acquire()
			t1 = time.time()
			self.exposure_timestamp = (t1 + t0) / 2.0
			# TO DO: Not sure what to ask for. Not explained in doc.
			# Either just Array or AsSafeArray. Need to try on the actual camera.
			arr = self.im.AsSafeArray
		except:
			raise
			#raise RuntimeError('Camera Acquisition Error in getting array')
		arr = self.modifyImage(arr)
		return arr

	def modifyImage(self, arr):
		self.image_metadata = self.im.MetaData
		rk = self.getConfig('readout')
		try:
			arr.shape = (self.limit_dim[rk]['y'],self.limit_dim[rk]['x'])
			#arr = numpy.flipud(arr)
		except AttributeError, e:
			print 'comtypes did not return an numpy 2D array, but %s' % (type(arr))
		except Exception, e:
			arr = None
			raise
		#Offset to apply to get back the requested area
		readout_offset = self.getReadoutOffset(rk, self.offset)
		try:
			if self.dimension['x'] < self.limit_dim[rk]['x']:
				arr=arr[:,readout_offset['x']:readout_offset['x']+self.dimension['x']]
			if self.dimension['y'] < self.limit_dim[rk]['y']:
				arr=arr[readout_offset['y']:readout_offset['y']+self.dimension['y'],:]
		except Exception, e:
			print 'croping %s to offset %s and dim %s failed' %(self.limit_dim, self.readout_offset,self.dimension)
			raise
			arr = None
		# TO DO: Maybe need to scale ?
		return arr

	def getRetractable(self):
		return True

	def getInserted(self):
		if self.getRetractable():
			return self.camera.IsInserted()
		else:
			return True

	def setInserted(self, value):
		# return if already at this insertion state
		if not self.getRetractable() or not (value ^ self.getInserted()):
			return
		if value:
			sleeptime = 5
			self.camera.Insert()
		else:
			sleeptime = 1
			self.camera.Retract()
		time.sleep(sleeptime)

	def getEnergyFiltered(self):
		return False

class Falcon(FeiCam):
	name = 'Falcon3EC'
	camera_name = 'BM-Falcon'
	binning_limits = [1,2,4]

	def __init__(self):
		super(Falcon,self).__init__()
		self.dfd = self.camera_settings.DoseFractionsDefinition
		self.save_frames = False
		self.frames_name = None
		#self.frame_rate = 4.0
		self.dosefrac_frame_time = 0.200
		self.record_precision = 0.100
		self.readout_delay_ms = 0
		self.align_frames = False
		self.align_filter = 'None'
		self.initFrameConfig()

	def initFrameConfig(self):
		self.frameconfig = falconframe.FalconFrameRangeListMaker(False)
		raw_frame_dir = self.camera_settings.PathToImageStorage #read only
		self.frameconfig.setBaseFramePath(raw_frame_dir)

	def setInserted(self, value):
		super(Falcon,self).setInserted(value)
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
		'''
		This is number of the output frames. Only meaningful after getImage.
		'''
		if self.save_frames:
			return self.frameconfig.getNumberOfFrameBins()
		else:
			return 0 # TO DO: Findout what it gives.

	def calculateMovieExposure(self):
		'''
		Movie Exposure is the exposure time to set to Falcon3FrameRangeMaker in ms
		'''
		self.movie_exposure = self.exposure
		self.frameconfig.setExposureTime(self.movie_exposure / 1000.0)

	def getReadoutDelay(self):
		'''
		Integrated image readout delay is always base_frame_time.
		There is no way to change it.
		'''
		return None

	def setUseFrames(self, frames):
		pass

	def getUseFrames(self):
		return None

	def setFrameTime(self,ms):
		seconds = ms / 1000.0
		self.dosefrac_frame_time = seconds

	def getFrameTime(self):
		# TO DO: Find out if need fractional millisecond.
		ms = self.dosefrac_frame_time * 1000.0
		return ms

	def getPreviousRawFramesName(self):
		return self.frames_name

	def custom_setup(self):
		self.calculateMovieExposure()
		movie_exposure_second = self.movie_exposure/1000.0
		self.camera_settings.ExposureTime = movie_exposure_second
		max_nframes = self.camera_settings.CalculateNumberOfFrames()
		frame_time_second = self.dosefrac_frame_time
		if self.save_frames:
			# Use all available frames
			rangelist = self.frameconfig.makeRangeListFromNumberOfBaseFramesAndFrameTime(max_nframes,frame_time_second)
			self.frames_name = self.frameconfig.getFrameDirName()
			self.camera_settings.SubPathPattern = self.frames_name
		else:
			rangelist = []
			self.frames_name = None
		self.dfd.Clear()
		for i in range(len(rangelist)):
			self.dfd.AddRange(rangelist[i][0],rangelist[i][1])

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

	def setFullCameraSetup(self):
		# workaround to offset image problem
		no_crop = {'x':0,'y':0}
		self.setOffset(no_crop)
		camsize = self.getCameraSize()
		binning = self.getBinning()
		full_dim = {'x': camsize['x']/binning['x'],'y':camsize['y']/binning['y']}
		original_dim = self.getDimension()
		self.setDimension(full_dim)
		return original_dim

	def _getImage(self):
		crop = self.getOffset()
		original_dimension = self.setFullCameraSetup()

		# super (or self.as_super as used in de.py) does not work in proxy call
		# copy the parent code here
		try:
			self.finalizeSetup()
			self.custom_setup()
		except:
			raise
			raise RuntimeError('Error setting camera acquisition parameters')

		t0 = time.time()

		try:
			self.im = self.csa.Acquire()
			t1 = time.time()
			self.exposure_timestamp = (t1 + t0) / 2.0
			# TO DO: Not sure what to ask for. Not explained in doc.
			# Either just Array or AsSafeArray. Need to try on the actual camera.
			arr = self.im.AsSafeArray
		except:
			raise
			#raise RuntimeError('Camera Acquisition Error in getting array')
		arr = self.modifyImage(arr)
		# END copy the parent code here

		image = arr
		if type(image).__module__!='numpy':
			return image
		# workaround to offset image problem
		self.setOffset(crop)
		self.setDimension(original_dimension)
		startx = self.getOffset()['x']
		starty = self.getOffset()['y']
		if startx != 0 or starty != 0:
			endx = self.dimension['x'] + startx
			endy = self.dimension['y'] + starty
			image = image[starty:endy,startx:endx]
		print 'modified shape',image.shape
		return image

	def getUseFrames(self):
				return (self.start_frame_number,self.end_frame_number)

