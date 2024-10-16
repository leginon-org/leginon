#import comtypes.client
import os
import subprocess
import glob
import shutil
import sys
import numpy

from pyscope import ccdcamera
import time
from pyscope import falconframe
from pyami import moduleconfig

try:
	from comtypes.safearray import safearray_as_ndarray
	USE_SAFEARRAY_AS_NDARRAY = True
except ImportError:
	USE_SAFEARRAY_AS_NDARRAY = False

SIMULATION = False
if SIMULATION:
	from . import simscripting
	connection = simscripting.Connection()
else:
	from pyscope import tia_display
	import comtypes
	import comtypes.client
	from pyscope import fei_advscripting
	connection = fei_advscripting.connection

READOUT_FULL = 0
READOUT_HALF = 1
READOUT_QUARTER = 2

configs = moduleconfig.getConfigured('fei.cfg')
## create a single connection to TIA COM object.
## Muliple calls to get_feiadv will return the same connection.
## Store the handle in the com module, which is safer than in
## this module due to multiple imports.

class FeiCam(ccdcamera.CCDCamera):
	name = 'FEICAM'
	camera_name = 'FEI_CAM'
	intensity_averaged = False

	base_fake_image = numpy.array(
[[-1.19424753,  1.4246904 , -0.93985889,  0.60135849,  0.27857971,
        -1.65301365,  1.04678336, -1.52532131],
       [-1.31055292, -1.64913688, -0.02365123,  0.66956679, -0.65988101,
         0.9513427 , -0.13423738,  0.33800944],
       [-1.1071589 ,  0.88239252,  0.10997026, -1.18640795,  0.61022063,
         0.81224024, -0.16747269,  0.00719223],
       [-0.90773998,  1.7711954 , -0.22341715,  1.77620855, -1.31179014,
         0.41032037,  0.0359722 ,  0.54127201],
       [-0.93403768, -0.68054982,  0.91282793, -0.3759068 , -0.90186899,
         0.25927322,  0.45464985,  0.45113749],
       [ 0.90185984,  0.61578781, -0.6812698 , -0.51314294,  1.5032234 ,
        -0.65909159,  2.16388489, -0.68847963],
       [-0.85829773, -2.44494674, -0.50517834,  0.6213358 ,  0.9792851 ,
         0.44794129,  0.76906529,  1.45588215],
       [ 0.43612393, -0.27890367, -0.11642871, -0.15955607, -2.52247377,
         0.62344606,  0.42410922,  1.02661867]])

	def __init__(self):
		self.unsupported = []
		ccdcamera.CCDCamera.__init__(self)
		self.save_frames = False
		self.batch = False
		self.frames_name_set_by_leginon=False
		self._connectToFEIAdvScripting()
		# set binning first so we can use it
		self.setCameraBinnings()
		self.setReadoutLimits()
		self.initSettings()
		self.setFrameFormatFromConfig()
		self.setUseCameraQueue()
		if not SIMULATION:
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
		if optionname not in list(configs.keys()):
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
		self.frame_format = 'mrc'
		self.save_frames = False
		self.align_frames = False
		self.save8x8 = False

	def setReadoutLimits(self):
		readout_dicts = {READOUT_FULL:1,READOUT_HALF:2,READOUT_QUARTER:4}
		self.sorted_readout_keys = (READOUT_QUARTER, READOUT_HALF, READOUT_FULL)
		size = self.getCameraSize()
		# before binning
		self.limit_dim = {}
		self.limit_off = {}
		for k in self.sorted_readout_keys:
			self.limit_dim[k] = {'x': int(size['x']/readout_dicts[k]), 'y': int(size['y']/readout_dicts[k])}
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
		self.binning_limit_objs= self.camera_capabilities.SupportedBinnings
		count = self.binning_limit_objs.Count
		binning_limits = []
		for index in range(count):
			binning_limits.append(self.binning_limit_objs[index].Width)
		self.binning_limits = binning_limits

	def setFrameFormatFromConfig(self):
		'''
		Default format is mrc.  Electron counting camera can use EER.
		Even if this is set to eer, camera without such capacity
		will still saves mrc
		'''
		fformat = 'mrc'
		try:
			# older advanced tem scripting does not have this property
			# nor the capacity.
			if self.camera_capabilities.SupportsEER:
				config_eer = self.getFeiConfig('camera','save_eer')
				if config_eer is True:
					fformat = 'eer'
					self.camera_settings.EER = True
		except:
			pass
		self.frame_format = fformat

	def setUseCameraQueue(self):
		self.use_queue = False

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

	def getFastSave(self):
		# Fastsave saves a small image arrary for frame camera to reduce handling time.
		return self.save8x8

	def setFastSave(self, state):
		# Fastsave saves a smaller image arrary for frame camera to reduce handling time.
		self.save8x8 = state

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
			connection = simscripting.get_feiadv_sim()
		else:
			connection = fei_advscripting.get_feiadv()
		self.instr = connection.instr
		self.csa = connection.csa
		try:
			self.ef = self.instr.EnergyFilter
		except Exception as e:
			self.ef = None
		# setCamera
		this_camera = self.getCamera()
		if this_camera is None:
			raise ValueError('%s not found' % self.camera_name)
		# set to this camera
		self.csa.Camera = this_camera
		# set attributes
		self.camera = this_camera
		self.camera_settings = self.csa.CameraSettings
		self.camera_capabilities = self.camera_settings.Capabilities

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

	def _getConfig(self, param):
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
		if value not in self.getExposureTypes():
			raise ValueError('invalid exposure type')
		self.exposuretype = value

	def getPixelSize(self):
		p = self.camera.PixelSize #in meters
		return {'x': p.Width, 'y': p.Height}

	def _getReadoutAreaKey(self,unbindim, off):
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

	def _getReadoutOffset(self, key, binned_full_off):
		limit_off = self.limit_off[key]
		return {'x':binned_full_off['x']-limit_off['x']//self.binning['x'],'y':binned_full_off['x']-limit_off['y']//self.binning['y']}

	def finalizeSetup(self):
		# final bin
		binning = self.binning

		# final range
		unbindim = {'x':self.dimension['x']*binning['x'], 'y':self.dimension['y']*binning['y']}
		unbinoff = {'x':self.offset['x']*binning['x'], 'y':self.offset['y']*binning['y']}
		readout_key = self._getReadoutAreaKey(unbindim, unbinoff)
		exposure = self.exposure/1000.0

		# send it to camera
		self.setConfig(binning= binning, readout=readout_key, exposure=exposure)

	def custom_setup(self):
		'''
		Camrea specific setup
		'''
		pass

	def waitForCameraReady(self):
		'''
		Wait for acquisition set blocking asynchronous process to finish
		'''
		while self.csa.IsActive:
			time.sleep(0.1)

	def getImage(self):
		# The following is copied from ccdcamera.CCDCamera since
		# super (or self.as_super as used in de.py) does not work in proxy call
		t0 = time.time()
		# BUG: IsActive only detect correctly with frame saving, not
		# camera availability
		if self.use_queue and self.save_frames:
			self.batch = True
		else:
			self.batch = False
		while self.csa.IsActive:
			time.sleep(0.1)
		if self.readoutcallback:
			name = str(time.time())
			self.registerCallback(name, self.readoutcallback)
			self.backgroundReadout(name)
		else:
			if self.getExposureType() == 'dark':
				result=self._getFakeDark()
			elif self.getExposureType() != 'norm':
				result=self._getImage()
				if not self.batch:
					self.csa.Wait()
			else:
				result= self._getSavedNorm()
			return result

	def _getSafeArray(self):
		# 64-bit pyscope/safearray does not work with newer 64-bit comtypes installation.
		# use safearray_as_ndarray instead.
		if USE_SAFEARRAY_AS_NDARRAY:
			with safearray_as_ndarray:
				return self.im.AsSafeArray
		else:
			return self.im.AsSafeArray

	def _modifyArray(self, arr):
		rk = self._getConfig('readout')
		# 64-bit pyscope/safearray does not work with newer 64-bit comtypes installation.
		# use safearray_as_ndarray instead.
		arr = arr.reshape((self.limit_dim[rk]['y']//self.binning['y'],self.limit_dim[rk]['x']//self.binning['x']))
		if USE_SAFEARRAY_AS_NDARRAY:
			arr = arr.T
		return arr

	def getNormImagePath(self):
		return None

	def _getSavedNorm(self):
		'''
		Return image array from saved image.
		'''
		try:
			self.finalizeSetup()
			self.custom_setup()
		except Exception as e:
			if self.getDebugCamera():
				print('Camera setup',e)
			raise RuntimeError('Error setting camera parameters: %s' % (e,))
		normpath = self.getNormImagePath()
		if not normpath:
			raise RuntimeError('Error finding saved norm image')
		if self.getDebugCamera():
			print('loading', normpath)
		import tifffile
		tif = tifffile.TIFFfile(normpath)
		arr = tif.asarray()
		self.image_metadata = {}
		if self.getDebugCamera():
			print('got arr and to modify')
		arr = self.modifyImage(arr)
		return arr

	def _getFakeDark(self):
		'''
		Return image array at zeros
		'''
		try:
			self.finalizeSetup()
			self.custom_setup()
		except Exception as e:
			if self.getDebugCamera():
				print('Camera setup',e)
			raise RuntimeError('Error setting camera parameters: %s' % (e,))
		rk = self._getConfig('readout')
		limit_dim = self.limit_dim[rk]
		arr = numpy.zeros((limit_dim['y'],limit_dim['x']))
		self.image_metadata = {}
		if self.getDebugCamera():
			print('got arr and to modify')
		arr = self.modifyImage(arr)
		return arr

	def _getImage(self):
		'''
		Acquire an image using the setup for this client.
		'''
		try:
			self.finalizeSetup()
			self.custom_setup()
		except Exception as e:
			if self.getDebugCamera():
				print('Camera setup',e)
			raise RuntimeError('Error setting camera parameters: %s' % (e,))

		t0 = time.time()

		#Queue has no wait at start.
		if not self.batch:
			self.csa.Wait()
		if self.getDebugCamera():
			print('done waiting before acquire')
		retry = False
		reason = ''
		try:
			self.im = self.csa.Acquire()
			t1 = time.time()
			self.exposure_timestamp = (t1 + t0) / 2.0
		except Exception as e:
			if self.getDebugCamera():
				print('Camera acquire:',e)
				print(self.camera_settings.ExposureTime)
			if self.getSaveRawFrames() and 'Timeout' in e.text:
				# dose fractionation queue may timeout on the server. The next acquisition
				# is independent enough that we allow it to retry.
				#TODO: only needed parameter settings retry if the first in queue.
				reason = 'Falcon WaitForImageReady Timeout'
				retry = True
			if self.getAlignFrames() and self.getSaveRawFrames() and 'The parameter is incorrect' in e.text:
				# dose fractionation definition range list is modified by the program.
				#framecount = self.dfd.Count
				#for i in range(framecount):
				#	print('%d,%d' % (self.dfd[i].Begin, self.dfd[i].End))
				reason='Parameter Correction for internal alignment'
				retry = True
			if retry == True:
				try:
					self.im = self.csa.Acquire()
				except Exception as e:
					raise RuntimeError('Error camera acquiring after retry: %s--%s' % (reason,e,))
			else:
				raise RuntimeError('Error camera acquiring: %s' % (e,))
		# If getSafeArray, it slows down as if not done.  Therefore return a fake 8x8
		if self.batch and self.save8x8 and ((hasattr(self, 'save_frames') and self.save_frames) or (hasattr(self, 'align_frames') and self.algn_frames)):
			if self.getDebugCamera():
				print('fake 8x8')
			# This is 0.20 s faster than get array and then make fake for 1 s exposure.
			fake_std = 50
			fake_mean = 4000
			arr = self.base_fake_image*fake_std + fake_mean*numpy.ones((8,8))
			return arr
		try:
			arr = self._getSafeArray()
		except Exception as e:
			if self.getDebugCamera():
				print('Camera array:',e)
			raise RuntimeError('Camera Error in getting array: %s' % (e,))
		if isinstance(arr,type(None)):
			if self.getDebugCamera():
				print('No array in memory, yet. Try again.')
			# TODO: maybe only do this when queue ends.
			if not self.batch:
				self.csa.Wait()
			try:
				arr = self._getSafeArray()
			except Exception as e:
				if self.getDebugCamera():
					print('Camera array 2nd try:',e)
				raise RuntimeError('Camera Error in getting array: %s' % (e,))
		if not SIMULATION:
			self.image_metadata = self.getMetaDataDict(self.im.MetaData)
		else:
			self.image_metadata = {}
		# TODO: maybe generate this from valid older images ?
		if hasattr(self, 'save_frames') and hasattr(self,'align_frames') and (self.save_frames or self.align_frames) and self.save8x8:
			arr = self.base_fake_image*arr.std() + arr.mean()*numpy.ones((8,8))
			return arr
		if self.getDebugCamera():
			print('got arr and to modify')
		arr = self.modifyImage(arr)
		return arr

	def modifyImage(self, arr):
		rk = self._getConfig('readout')
		# reshape to 2D
		try:
			arr = self._modifyArray(arr)
		except AttributeError as e:
			if self.getDebugCamera():
				print('comtypes did not return an numpy 2D array, but %s' % (type(arr)))
		except Exception as e:
			arr = None
			if self.getDebugCamera():
				print('modify array error',e)
			raise
		#Offset to apply to get back the requested area
		readout_offset = self._getReadoutOffset(rk, self.offset)
		try:
			if self.dimension['x'] < arr.shape[1]:
				arr=arr[:,readout_offset['x']:readout_offset['x']+self.dimension['x']]
			if self.dimension['y'] < arr.shape[0]:
				arr=arr[readout_offset['y']:readout_offset['y']+self.dimension['y'],:]
		except Exception as e:
			if self.getDebugCamera():
				print('croping %s to offset %s and dim %s failed' %(self.limit_dim, self.readout_offset,self.dimension))
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
				if bits[0] not in list(mdict.keys()):
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
			except ValueError as e:
				print('TIA display %s can not be closed' % self.display_name)
		self._clickAcquire(exposure_time_s)

	def stopMovie(self, filename, exposure_time_ms):
		exposure_time_s = exposure_time_ms/1000.0
		self._clickAcquire(exposure_time_s)
		self.display_name = self.tia_display.getActiveDisplayWindowName()
		print('movie name: %s' % filename)
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

	def getSystemGainDarkCorrected(self):
		# deprecated in v3.6
		return True

	def getSystemDarkSubtracted(self):
		return True

	def getFrameGainCorrected(self):
		return True

	def getSumGainCorrected(self):
		return True

class Ceta(FeiCam):
	name = 'Ceta'
	camera_name = 'BM-Ceta'
	binning_limits = [1,2,4]
	intensity_averaged = False

class Falcon3(FeiCam):
	name = 'Falcon3'
	camera_name = 'BM-Falcon'
	binning_limits = [1,2,4]
	electron_counting = False
	base_frame_time = 0.025 # seconds
	physical_frame_rate = 40 # frames per second
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
		self.frameconfig.setBaseFrameTime(self.base_frame_time)
		falcon_image_storage = self.camera_settings.PathToImageStorage #read only
		falcon_image_storage = 'z:\\TEMScripting\\BM-Falcon\\'
		if 'falcon_image_storage_path' in list(configs['camera'].keys()) and configs['camera']['falcon_image_storage_path']:
			falcon_image_storage = configs['camera']['falcon_image_storage_path']
		print('Falcon Image Storage Server Path is ', falcon_image_storage)
		sub_frame_dir = self.getFeiConfig('camera','frame_subpath')
		try:
			self.frameconfig.setFeiImageStoragePath(falcon_image_storage)
			self.frameconfig.setBaseFramePath(sub_frame_dir)
		except:
			raise
		if 'frame_name_prefix' in configs['camera'].keys():
			prefix = configs['camera']['frame_name_prefix']
			self.frameconfig.setFrameNamePrefix(prefix)
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

	def getEerRenderDefault(self):
		'''
		Return the multiplication factor of eer raw frame to falcon
		program CalculateNumberOfFrames method result.
		'''
		# Falcon4: CalculateNumberOfFrames * 7 =  eer nframes
		# Falcon4i: CalculateNumberOfFrames * 9 =  eer nframes
		if self.getSaveEer():
			value = self.getFeiConfig('camera','eer_render')
			try:
				return int(value)
			except TypeError:
				return 7 # default
		return 0

	def getNumberOfFrames(self):
		'''
		This is number of the output frames. Only meaningful after getImage.
		'''
		if self.save_frames:
			if self.frame_format == 'mrc':
				return self.frameconfig.getNumberOfFrameBins()
			if self.frame_format == 'eer':
				# set camera settings so we can get the calculated value
				# before the real getImage
				self.camera_settings.EER = True
				rendered_nframes = self.camera_settings.CalculateNumberOfFrames()
				return rendered_nframes*self.getEerRenderDefault()
		else:
			return 0

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
		if self.frame_format == 'eer' and self.electron_counting:
			# EER is handled as if sampled at physical_frame_rate
			ms = 1000.0 / self.physical_frame_rate
		else:
			# custom_setup may modify this if bins are not even.
			ms = self.dosefrac_frame_time * 1000.0
		return ms

	def makeNextRawFramesName(self):
		self.frames_name_set_by_leginon=True
		return self._makeNextRawFramesName()

	def _makeNextRawFramesName(self):
		sub_frame_dir = self.frameconfig.getBaseFramePath()
		# use createFramePath because some attributes need to be set
		self.frameconfig.createFramePath(sub_frame_dir)
		self.frames_name = self.frameconfig.getFrameDirName()
		return self.frames_name

	def unsetNextRawFramesName(self):
		self.frames_name_set_by_leginon=False

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
			print('is counting: ', self.electron_counting)
		self.setElectronCounting(self.electron_counting)
		self.calculateMovieExposure()
		movie_exposure_second = self.movie_exposure/1000.0
		self.camera_settings.ExposureTime = movie_exposure_second
		if self.save_frames:
			self.camera_settings.AlignImage = self.align_frames
		frame_time_second = self.dosefrac_frame_time
		if self.save_frames:
			if not self.frames_name_set_by_leginon:
				self._makeNextRawFramesName() # this sets self.rawframesname
			else:
				# use rawframesname already set
				pass
			# EER only works in counting mode
			if self.frame_format == 'eer' and self.electron_counting:
				self.camera_settings.EER = True
				# EER only works with self.dfd is Clear
				rangelist = []
				# EER is handled as if sampled at physical_frame_rate
				self.dosefrac_frame_time = 1.0 / self.physical_frame_rate
			else:
				# non-electron_counting can not be saved as EER.
				if self.frame_format == 'eer':
					# make sure EER is not set at camera
					self.camera_settings.EER = False
				# Use all available frames
				max_nframes = self.camera_settings.CalculateNumberOfFrames()
				if self.getDebugCamera():
					print('n base frames', max_nframes)
				rangelist = self.frameconfig.makeRangeListFromNumberOfBaseFramesAndFrameTime(max_nframes,frame_time_second)
				if self.getDebugCamera():
					print('rangelist', rangelist, len(rangelist))
					print('#base', map((lambda x:x[1]-x[0]),rangelist))
				if rangelist:
					# modify frame time in case of uneven bins
					self.dosefrac_frame_time = movie_exposure_second / len(rangelist)
			self.frames_pattern = self.frameconfig.getSubPathFramePattern()
			self.camera_settings.SubPathPattern = self.frames_pattern
		else:
			if self.frame_format == 'eer':
				# make sure EER is not set at camera
				self.camera_settings.EER = False
			rangelist = []
			self.frames_name = None
		self.dfd.Clear()
		for i in range(len(rangelist)):
			self.dfd.AddRange(rangelist[i][0],rangelist[i][1])

	def getFrameGainCorrected(self):
		# Only eer movies need to use gain reference
		return not self.frame_format == 'eer'

	def getFrameFlip(self):
		'''
		Frame Flip is defined as up-down flip
		'''
		flip = self.getFeiConfig('camera','eer_frame_flip')
		# so far only certain version of software and eer needs this.
		if self.save_frames and self.frame_format == 'eer' and flip is not None:
			return flip
		return False

	def getFrameRotate(self):
		'''
		Frame Rotate direction is defined as x to -y rotation applied after up-down flip
		'''
		rotate = self.getFeiConfig('camera','eer_frame_rotate')
		# so far only certain version of software and eer needs this.
		if self.save_frames and self.frame_format == 'eer' and rotate is not None:
			return rotate
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
	base_frame_time = 0.025 # seconds
	physical_frame_rate = 40 # frames per second

	def getUseFrames(self):
		# with the possibility of using EER, this is better left
		# as None and use NumberOfFrames in frame processing
		return None

class Falcon4EC(Falcon3EC):
	name = 'Falcon4EC'
	camera_name = 'BM-Falcon'
	binning_limits = [1,2,4]
	electron_counting = True
	intensity_averaged = False
	base_frame_time = 0.02907 # seconds
	physical_frame_rate = 250 # rolling shutter frames per second

	def setExposureTime(self,ms):
		self.exposure = float(ms)
		self.calculateMovieExposure()
		movie_exposure_second = self.movie_exposure/1000.0
		self.camera_settings.ExposureTime = movie_exposure_second

	def setUseCameraQueue(self):
		use_queue = False
		try:
				config_queue = self.getFeiConfig('camera','use_camera_queue')
				if config_queue is True:
					use_queue = True
		except:
			pass
		self.use_queue = use_queue

	def setInserted(self, value):
		super(Falcon4EC, self).setInserted(value)

	def getExposureTypes(self):
		"""
		norm type is used to retrieve norm image, not a real exposure.
		"""
		return ['normal', 'dark','norm']

	def getSaveEer(self):
		return self.frame_format == 'eer' and self.electron_counting

	def getNormImagePath(self):
		"""
		return the path for the latest gain file.
		"""
		norm_dir = self.getFeiConfig('camera','eer_gain_reference_dir')
		if not os.path.isdir(norm_dir):
			return None
		pattern = os.path.join(norm_dir,'*.gain')
		files = glob.glob(pattern)
		files.sort()
		if len(files) == 0:
			return None
		return files[-1]

class Selectris(object):
	def setup(self, ef_pointer):
		self.ef = ef_pointer
		if not self.ef:
			raise ValueError('Selctris energy filter interface not initialized. Check fei.cfg')
		self.slit = self.ef.Slit
		self.ht_shift = self.ef.HighTensionEnergyShift

	def getEnergyFiltered(self):
		'''
		Return True if energy filter is controlled through this.
		'''
		return True

	def getEnergyFilter(self):
		'''
		Return True if controlled energy filter is enabled
		with slit in
		'''
		return self.slit.IsInserted

	def setEnergyFilter(self, value):
		'''
		Enable/Disable controled energy filter
		by retracting the slit
		'''
		if self.getEnergyFilter() == value:
			return
		if value:
			error = self.slit.Insert()
		else:
			error = self.slit.Retract()
		if error:
			raise RuntimeError('unable to set energy filter slit position: %s' % error)

	def getEnergyFilterWidth(self):
		'''
		Return  energe filter slit width in eV.
		'''
		return self.slit.Width

	def getEnergyFilterWidthRange(self):
		return self.slit.WidthRange.Begin, self.slit.WidthRange.End

	def setEnergyFilterWidth(self, value):
		'''
		Set energe filter slit width in eV.
		'''
		value = float(value)
		begin,end = self.getEnergyFilterWidthRange()
		if value < begin or value > end:
			raise RuntimeError('energy filter width %.1f out of range' % value)
		self.slit.Width = value

	def getEnergyFilterOffset(self):
		'''
		Return energy filter high tension offset.
		'''
		return self.ht_shift.EnergyShift

	def getEnergyShiftRange(self):
		return self.ht_shift.EnergyShiftRange.Begin, self.ht_shift.EnergyShiftRange.End

	def setEnergyFilterOffset(self, value):
		'''
		Set energe filter energy offset in eV. High tension energy shift is used.
		'''
		value = float(value)
		begin,end = self.getEnergyShiftRange()
		if value < begin or value > end:
			raise RuntimeError('energy filter offset %.1f out of range' % value)
		self.ht_shift.EnergyShift = value

class Falcon4ECef(Falcon4EC):
	name = 'Falcon4EC'
	camera_name = 'EF-Falcon'
	binning_limits = [1,2,4]
	electron_counting = True
	intensity_averaged = False
	base_frame_time = 0.02907 # seconds
	physical_frame_rate = 250 # rolling shutter frames per second

	def __init__(self):
		super(Falcon4ECef, self).__init__()
		if self.ef is None:
			raise RuntimeError('TFS energy filter not available')
		self.ef_control = Selectris()
		self.ef_control.setup(self.ef)
		for attr_name in dir(self.ef_control):
			if attr_name.startswith('get') or attr_name.startswith('set'):
				setattr(self,attr_name, getattr(self.ef_control,attr_name))
