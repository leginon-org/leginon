#import comtypes.client
import os
import subprocess
import glob
import shutil
import sys

import ccdcamera
import time
import simscripting
import falconframe
from pyscope import tia_display
from pyami import moduleconfig

try:
	from comtypes.safearray import safearray_as_ndarray
	USE_SAFEARRAY_AS_NDARRAY = True
except ImportError:
	USE_SAFEARRAY_AS_NDARRAY = False

SIMULATION = False
class FEIAdvScriptingConnection(object):
	instr = None
	csa = None
	cameras = []

if SIMULATION:
	# There is problem starting numpy in FEI 2.9 software as FEI version of python2.7 becomes the default.
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
def chooseTEMAdvancedScriptingName():
	if 'version' not in configs.keys() or 'tfs_software_version' not in configs['version'].keys():
		print 'Need version section in fei.cfg. Please update it'
		raw_input('Hit return to exit')
		sys.exit(0)
	version_text = configs['version']['tfs_software_version']
	bits = version_text.split('.')
	if len(bits) != 3 or not bits[1].isdigit():
		print 'Unrecognized Version number, not in the format of %d.%d.%d'
		raw_input('Hit return to exit')
	major_version = int(bits[0])
	minor_version = int(bits[1])
	if 'software_type' not in  configs['version'].keys():
		print 'Need software_type in version section in fei.cfg. Please update it'
		raw_input('Hit return to exit')
		sys.exit(0)
	software_type = lower(configs['version']['software_type'])
	if software_type == 'titan':
		# titan major version is one higher than talos
		major_version += 1
	if major_version > 2 or minor_version >= 15:
		return '2'
	else:
		return '1'

def get_feiadv():
	global connection
	if connection.instr is None:
		try:
			comtypes.CoInitializeEx(comtypes.COINIT_MULTITHREADED)
		except:
			comtypes.CoInitialize()
		type_name = 'TEMAdvancedScripting.AdvancedInstrument.' + chooseTEMAdvancedScriptingName()
		connection.instr = comtypes.client.CreateObject(type_name)
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
	intensity_averaged = False

	def __init__(self):
		self.unsupported = []
		ccdcamera.CCDCamera.__init__(self)
		self.save_frames = False
		self._connectToFEIAdvScripting()
		# set binning first so we can use it
		self.setCameraBinnings()
		self.setReadoutLimits()
		self.initSettings()
		self.tia_display = tia_display.TIA()

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

	def getDebugCamera(self):
		return self.getFeiConfig('debug','all') or self.getFeiConfig('debug','camera')

	def initSettings(self):
		self.dimension = self.getCameraSize()
		self.binning = {'x':1, 'y':1}
		self.offset = {'x':0, 'y':0}
		self.exposure = 500.0
		self.exposuretype = 'normal'
		self.start_frame_number = 1
		self.end_frame_number = None
		self.display_name = None

	def setReadoutLimits(self):
		readout_dicts = {READOUT_FULL:1,READOUT_HALF:2,READOUT_QUARTER:4}
		self.sorted_readout_keys = (READOUT_QUARTER, READOUT_HALF, READOUT_FULL)
		size = self.getCameraSize()
		# before binning
		self.limit_dim = {}
		self.limit_off = {}
		for k in self.sorted_readout_keys:
			self.limit_dim[k] = {'x': size['x']/readout_dicts[k], 'y': size['y']/readout_dicts[k]}
			self.limit_off[k] = {'x': int((size['x']-self.limit_dim[k]['x'])/2.0), 'y':int((size['y']-self.limit_dim[k]['y'])/2.0)}
		self.readout_offset = {'x':0,'y':0}

	def getCameraModelName(self):
		return self.camera_name

	def getIntensityAveraged(self):
		return self.intensity_averaged

	def setDimension(self, value):
		self.dimension = value

	def getDimension(self):
		return self.dimension

	def setCameraBinnings(self):
		'''
		Read from camera capabilities the supported binnings and
		set self.binning_limits and the self.binning_limit_objs
		'''
		self.binning_limit_objs= self.capabilities.SupportedBinnings
		count = self.binning_limit_objs.Count
		binning_limits = []
		for index in range(count):
			binning_limits.append(self.binning_limit_objs[index].Width)
		self.binning_limits = binning_limits

	def getCameraBinnings(self):
		return self.binning_limits

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
		self.capabilities = self.camera_settings.Capabilities

	def setConfig(self, **kwargs):
		'''
		Set commera settings.
		readout is an index 0:Full,1:Half, 2:Quarter.
		Binning is calculated from that.
		exposure is the exposure time in seconds

		'''
		try:
			if 'readout' in kwargs:
				readout = kwargs['readout']
				self.camera_settings.ReadoutArea = readout
			if 'exposure' in kwargs:
				exposure = kwargs['exposure']
				self.camera_settings.ExposureTime = exposure
			if 'binning' in kwargs:
				binning = kwargs['binning']
				# binning can only be set by supported binning objects
				b_index = self.binning_limits.index(binning['x'])
				self.camera_settings.Binning = self.binning_limit_objs[b_index]
		except:
			raise

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
		p = self.camera.PixelSize #in meters
		return {'x': p.Width, 'y': p.Height}

	def getReadoutAreaKey(self,unbindim, off):
		size = self.getCameraSize()
		if unbindim['x']+off['x'] > size['x'] or unbindim['y']+off['y'] > size['y']:
			raise ValueError('defined readout area outside the camera')
		for k in self.sorted_readout_keys:
			limit_off = self.limit_off[k]
			limit_dim = self.limit_dim[k]
			if (off['x'] >= limit_off['x']
				and off['y'] >= limit_off['y']
				and	off['x']+unbindim['x'] <= limit_dim['x']+limit_off['x']
				and off['y']+unbindim['y'] <= limit_dim['y']+limit_off['y']):
				return k
		raise ValueError('Does not fit any defined readout area')

	def getReadoutOffset(self, key, binned_full_off):
		limit_off = self.limit_off[key]
		return {'x':binned_full_off['x']-limit_off['x']/self.binning['x'],'y':binned_full_off['x']-limit_off['y']/self.binning['y']}

	def finalizeSetup(self):
		# final bin
		binning = self.binning

		# final range
		unbindim = {'x':self.dimension['x']*binning['x'], 'y':self.dimension['y']*binning['y']}
		unbinoff = {'x':self.offset['x']*binning['x'], 'y':self.offset['y']*binning['y']}
		readout_key = self.getReadoutAreaKey(unbindim, unbinoff)
		exposure = self.exposure/1000.0

		# send it to camera
		self.setConfig(binning= binning, readout=readout_key, exposure=exposure)

	def custom_setup(self):
		'''
		Camrea specific setup
		'''
		pass

	def getImage(self):
		# The following is copied from ccdcamera.CCDCamera since
		# super (or self.as_super as used in de.py) does not work in proxy call
		t0 = time.time()
		# BUG: IsActive only detect correctly with frame saving, not
		# camera availability
		while self.csa.IsActive:
			time.sleep(0.1)
		if self.readoutcallback:
			name = str(time.time())
			self.registerCallback(name, self.readoutcallback)
			self.backgroundReadout(name)
		else:
			result=self._getImage()
			self.csa.Wait()
			return result

	def _getSafeArray(self):
		# 64-bit pyscope/safearray does not work with newer 64-bit comtypes installation.
		# use safearray_as_ndarray instead.
		if USE_SAFEARRAY_AS_NDARRAY:
			with safearray_as_ndarray:
				return self.im.Data.Array
		else:
			return self.im.Data.Array

	def _modifyArray(self, arr):
		# 64-bit pyscope/safearray does not work with newer 64-bit comtypes installation.
		# use safearray_as_ndarray instead.
		arr = arr.reshape((self.limit_dim[rk]['y']/self.binning['y'],self.limit_dim[rk]['x']/self.binning['x']))
		if USE_SAFEARRAY_AS_NDARRAY:
			arr = arr.T
		return arr

	def _getImage(self):
		'''
		Acquire an image using the setup for this client.
		'''
		try:
			self.finalizeSetup()
			self.custom_setup()
		except Exception, e:
			if self.getDebugCamera():
				print 'Camera setup',e
			raise RuntimeError('Error setting camera parameters: %s' % (e,))

		t0 = time.time()

		#TODO: Check if this is going to be an issue
		self.csa.Wait()
		if self.getDebugCamera():
			print 'done waiting before acquire'
		retry = False
		reason = ''
		try:
			self.im = self.csa.Acquire()
			t1 = time.time()
			self.exposure_timestamp = (t1 + t0) / 2.0
		except Exception, e:
			if self.getDebugCamera():
				print 'Camera acquire:',e
				print self.camera_settings.ExposureTime
			if self.getSaveRawFrames() and 'Timeout' in e.text:
				# dose fractionation queue may timeout on the server. The next acquisition
				# is independent enough that we allow it to retry.
				reason = 'Falcon WaitForImageReady Timeout'
				retry = True
			if self.getAlignFrames() and self.getSaveRawFrames() and 'The parameter is incorrect' in e.text:
				# dose fractionation definition range list is modified by the program.
				#framecount = self.dfd.Count
				#for i in range(framecount):
				#	print '%d,%d' % (self.dfd[i].Begin, self.dfd[i].End)
				reason='Parameter Correction for internal alignment'
				retry = True
			if retry == True:
				try:
					self.im = self.csa.Acquire()
				except Exception, e:
					raise RuntimeError('Error camera acquiring after retry: %s--%s' % (reason,e,))
			else:
				raise RuntimeError('Error camera acquiring: %s' % (e,))
		try:
			arr = self._getSafeArray()
		except Exception, e:
			if self.getDebugCamera():
				print 'Camera array:',e
			raise RuntimeError('Camera Error in getting array: %s' % (e,))
		if isinstance(arr,type(None)):
			if self.getDebugCamera():
				print 'No array in memory, yet. Try again.'
			self.csa.Wait()
			try:
				arr = self._getSafeArray()
			except Exception, e:
				if self.getDebugCamera():
					print 'Camera array 2nd try:',e
				raise RuntimeError('Camera Error in getting array: %s' % (e,))
		if not SIMULATION:
			self.image_metadata = self.getMetaDataDict(self.im.MetaData)
		else:
			self.image_metadata = {}
		if self.getDebugCamera():
			print 'got arr and to modify'
		arr = self.modifyImage(arr)
		return arr

	def modifyImage(self, arr):
		rk = self.getConfig('readout')
		# reshape to 2D
		try:
			arr = self._modifyArray(arr)
		except AttributeError, e:
			if self.getDebugCamera():
				print 'comtypes did not return an numpy 2D array, but %s' % (type(arr))
		except Exception, e:
			arr = None
			if self.getDebugCamera():
				print 'modify array error',e
			raise
		#Offset to apply to get back the requested area
		readout_offset = self.getReadoutOffset(rk, self.offset)
		try:
			if self.dimension['x'] < arr.shape[1]:
				arr=arr[:,readout_offset['x']:readout_offset['x']+self.dimension['x']]
			if self.dimension['y'] < arr.shape[0]:
				arr=arr[readout_offset['y']:readout_offset['y']+self.dimension['y'],:]
		except Exception, e:
			if self.getDebugCamera():
				print 'croping %s to offset %s and dim %s failed' %(self.limit_dim, self.readout_offset,self.dimension)
			raise
		# TO DO: Maybe need to scale ?
		if SIMULATION and self.getIntensityAveraged():
			arr = arr / (self.getExposureTime()/1000.0)
		return arr

	def getMetaDataDict(self,meta_obj):
		mdict = {}
		count = meta_obj.Count
		for i in range(count):
			key = meta_obj[i].Key
			v_string = meta_obj[i].ValueAsString
			try:
				#integer
				value = int(v_string)
			except (TypeError,ValueError):
				try:
					#float
					value = float(v_string)
				except:
					#boolean
					if v_string in ('FALSE','TRUE'):
						if v_string == 'FALSE':
							value = False
						else:
							value = True
					else:
						# string
						value = v_string
			if '.' in key:
				bits = key.split('.')
				if bits[0] not in mdict.keys():
					mdict[bits[0]]={}
				mdict[bits[0]][bits[1]]=value
			else:
				mdict[key]=value
		return mdict

	def getRetractable(self):
		return True

	def getInserted(self):
		if self.getRetractable():
			return self.camera.IsInserted
		else:
			return True

	def setInserted(self, value):
		# return if already at this insertion state
		if not self.getRetractable() or not (value ^ self.getInserted()):
			return
		if value:
			sleeptime = 5
			error_state=self.camera.Insert()
		else:
			sleeptime = 1
			error_state=self.camera.Retract()
		if error_state:
			raise RuntimeError('Can not alter insert state')
		time.sleep(sleeptime)

	def getEnergyFiltered(self):
		return False

	def startMovie(self, filename, exposure_time_ms):
		exposure_time_s = exposure_time_ms/1000.0
		if self.display_name:
			try:
				self.tia_display.closeDisplayWindow(self.display_name)
			except ValueError, e:
				print 'TIA display %s can not be closed' % self.display_name
		self._clickAcquire(exposure_time_s)

	def stopMovie(self, filename, exposure_time_ms):
		exposure_time_s = exposure_time_ms/1000.0
		self._clickAcquire(exposure_time_s)
		self.display_name = self.tia_display.getActiveDisplayWindowName()
		print 'movie name: %s' % filename
		time.sleep(exposure_time_s)
		self._saveMovie(filename)
		self._waitForSaveMoveDone()
		self._moveMovie()

	def _waitForSaveMoveDone(self):
		timeout = 120
		t0 = time.time()
		current_length = 0
		last_series_length = current_length
		while current_length < 2 or last_series_length < current_length:
			if time.time()-t0 > timeout:
				raise ValueError('Movie saving failed. File saving not finished after %d seconds.' % timeout)
			time.sleep(1.0)
			last_series_length = current_length
			current_length = self._findSeriesLength()
		# final value
		self.series_length = self._findSeriesLength()

	def _saveMovie(self, filename=''):
		exepath = self.getFeiConfig('camera','autoit_tia_export_series_exe_path')
		if exepath and os.path.isfile(exepath):
			if filename:
				self.target_code = filename.split('.bin')[0]
				# self.series_length should be 0 at this point
				self.series_length = self._findSeriesLength()
				subprocess.call("%s %s" % (exepath, self.target_code))
			else:
				raise ValueError('movie saving filename not provided')
		else:
			raise NotImplementedError()

	def _moveMovie(self):
		data_dir = self.getFeiConfig('camera','autoit_tia_exported_data_dir')
		new_dir = self.getFeiConfig('camera','tia_exported_data_network_dir')
		if not new_dir:
			return
		if not os.path.isdir(new_dir):
			raise ValueError('TIA exported data network Directory %s is not a directory' % (new_dir,))
		if data_dir == new_dir:
			# nothing to do
			return
		else:
			if not self.target_code:
				raise ValueError('movie target code not yet set')
			pattern = os.path.join(data_dir, '%s*.bin' % (self.target_code,))
			files = glob.glob(pattern)
			for f in files:
				shutil.move(f, new_dir)

	def _findSeriesLength(self):
		if not self.target_code:
			raise ValueError('movie target code not yet set')
		data_dir = self.getFeiConfig('camera','autoit_tia_exported_data_dir')
		pattern = os.path.join(data_dir, '%s*.bin' % (self.target_code,))
		length = len(glob.glob(pattern))
		return length

	def _clickAcquire(self, exposure_time_s=None):
		# default is not checking
		exepath = self.getFeiConfig('camera','autoit_tui_acquire_exe_path')
		if exepath and os.path.isfile(exepath):
			if exposure_time_s is not None:
				subprocess.call("%s %.3f" % (exepath, exposure_time_s))
			else:
				subprocess.call(exepath)
		else:
			raise NotImplementedError()

class Ceta(FeiCam):
	name = 'Ceta'
	camera_name = 'BM-Ceta'
	binning_limits = [1,2,4]
	intensity_averaged = False

	def getSystemGainDarkCorrected(self):
		return True

class Falcon3(FeiCam):
	name = 'Falcon3'
	camera_name = 'BM-Falcon'
	binning_limits = [1,2,4]
	electron_counting = False
	# non-counting Falcon3 is the only camera that returns array aleady averaged by frame
	# to keep values in more reasonable range.
	intensity_averaged = True

	def __init__(self):
		super(Falcon3,self).__init__()
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
		falcon_image_storage = self.camera_settings.PathToImageStorage #read only
		falcon_image_storage = 'z:\\TEMScripting\\BM-Falcon\\'
		if 'falcon_image_storage_path' is in configs['camera'] and configs['camera']['falcon_image_storage_path']:
			falcon_image_storage = configs['camera']['falcon_image_storage_path']
		print 'Falcon Image Storage Server Path is ', falcon_image_storage
		sub_frame_dir = self.getFeiConfig('camera','frame_subpath')
		try:
			self.frameconfig.setFeiImageStoragePath(falcon_image_storage)
			self.frameconfig.setBaseFramePath(sub_frame_dir)
		except:
			raise
		self.extra_protector_sleep_time = self.getFeiConfig('camera','extra_protector_sleep_time')

	def setInserted(self, value):
		super(Falcon3,self).setInserted(value)
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
		# custom_setup may modify this if bins are not even.
		ms = self.dosefrac_frame_time * 1000.0
		return ms

	def getPreviousRawFramesName(self):
		return self.frames_name

	def setElectronCounting(self,value):
		self.camera_settings.ElectronCounting = value

	def custom_setup(self):
		# Default not to align
		self.camera_settings.AlignImage = False
		if self.extra_protector_sleep_time:
			time.sleep(self.extra_protector_sleep_time)
		if self.getDebugCamera():
			print 'is counting: ', self.electron_counting
		self.setElectronCounting(self.electron_counting)
		self.calculateMovieExposure()
		movie_exposure_second = self.movie_exposure/1000.0
		self.camera_settings.ExposureTime = movie_exposure_second
		if self.save_frames:
			self.camera_settings.AlignImage = self.align_frames
		max_nframes = self.camera_settings.CalculateNumberOfFrames()
		if self.getDebugCamera():
			print 'n base frames', max_nframes
		frame_time_second = self.dosefrac_frame_time
		if self.save_frames:
			# Use all available frames
			rangelist = self.frameconfig.makeRangeListFromNumberOfBaseFramesAndFrameTime(max_nframes,frame_time_second)
			if self.getDebugCamera():
				print 'rangelist', rangelist
			if rangelist:
				# modify frame time in case of uneven bins
				self.dosefrac_frame_time = movie_exposure_second / len(rangelist)
			self.frames_pattern = self.frameconfig.getSubPathFramePattern()
			self.camera_settings.SubPathPattern = self.frames_pattern
			self.frames_name = self.frameconfig.getFrameDirName()
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
		return 0

	def getUseFrames(self):
		nframes = self.getNumberOfFrames()
		return tuple(range(nframes))

	def setAlignFrames(self, value):
		self.align_frames = bool(value)

	def getAlignFrames(self):
		return self.align_frames

class Falcon3EC(Falcon3):
	name = 'Falcon3EC'
	camera_name = 'BM-Falcon'
	binning_limits = [1,2,4]
	electron_counting = True
	intensity_averaged = False

class Falcon4EC(Falcon3EC):
	name = 'Falcon4EC'
	camera_name = 'BM-Falcon'
	binning_limits = [1,2,4]
	electron_counting = True
	intensity_averaged = False

	def setInserted(self, value):
		super(Falcon4EC, self).setInserted(value)
