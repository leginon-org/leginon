#!/usr/bin/env python
import ccdcamera
import time
import os
import shutil
import glob
import numpy

from pyami import moduleconfig, tvips

SIMULATION = False
class EMMENUScriptingConnection(object):
	instr = None
	csa = None
	cameras = []

import numpy

if SIMULATION:
	import simscripting
	connection = simscripting.Connection()
else:
	import comtypes
	import comtypes.client
	connection = EMMENUScriptingConnection()

READOUT_FULL = 0
READOUT_HALF = 1
READOUT_QUARTER = 2

configs = moduleconfig.getConfigured('tvips.cfg')
## create a single connection to COM object.
## Multiple calls to get_emmenu will return the same connection.
## Store the handle in the com module, which is safer than in
## this module due to multiple imports.
def get_emmenu():
	global connection
	if connection.instr is None:
		try:
			comtypes.CoInitializeEx(comtypes.COINIT_MULTITHREADED)
		except:
			comtypes.CoInitialize()
		connection.instr = comtypes.client.CreateObject('EMMENU4.EMMENUApplication.1')
	return connection

def get_emmenu_sim():
	connection.instr = connection.Instrument
	return connection

class EmMenuF416(ccdcamera.CCDCamera):
	name = 'Tietz F416'
	camera_name = 'Tietz F416'
	intensity_averaged = False
	binning_limits = [1,2,4]

	def __init__(self):
		self.unsupported = []
		ccdcamera.CCDCamera.__init__(self)
		self.save_frames = False
		self.nframes = 1
		self._connectToEMMENUScripting()
		# set binning first so we can use it
		self.initSettings()
		self.movie_aborted = False

	def __getattr__(self, name):
		# When asked for self.camera, instead return self._camera, but only
		# after setting the current camera id
		if name == 'camera':
			if self.camera_name is not None:
				self._ccd = self.getCamera()
			return self._ccd
		else:
			return ccdcamera.CCDCamera.__getattribute__(self, name)

	def getTvipsConfig(self,optionname,itemname=None):
		if optionname not in configs.keys():
			return None
		if itemname is None:
			return configs[optionname]
		else:
			if itemname not in configs[optionname]:
				return None
			return configs[optionname][itemname]

	def getDebugCamera(self):
		return self.getTvipsConfig('debug','all') or self.getTvipsConfig('debug','camera')

	def initSettings(self):
		self.dimension = self.getCameraSize()
		self.binning = {'x':1, 'y':1}
		self.offset = {'x':0, 'y':0}
		self.exposure = 500.0
		self.exposuretype = 'normal'
		self.start_frame_number = 1
		self.end_frame_number = None

	def getCameraModelName(self):
		return self.camera_name

	def getIntensityAveraged(self):
		return self.intensity_averaged

	def setDimension(self, value):
		self.dimension = value

	def getDimension(self):
		return self.dimension

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
		return self.vp1.SelectedCamera

	def _getConfigObject(self, name):
		print(self.instr)
		for c in range(self.instr.CameraConfigurations.Count):
			if self.instr.CameraConfigurations.Item(c+1).Name == name:
				return self.instr.CameraConfigurations.Item(c+1)
		#TODO: Need to add configuration, but don't know how, yet.

	def _connectToEMMENUScripting(self):
		'''
		Connects to the COM server
		'''
		if SIMULATION:
			connection = get_emmenu_sim()
		else:
			connection = get_emmenu()
		self.instr = connection.instr
		vps = connection.instr.Viewports
		if vps.Count < 1:
			# TODO : How to get a new view pointer ?
			pass
		self.vp1 = connection.instr.ViewPorts.Item(1)
		# TODO: setCamera
		this_camera = self.getCamera()
		if this_camera is None:
			raise ValueError('%s not found' % self.camera_name)
		# set attributes
		self.camera = this_camera
		self.vp1.Configuration = 'Leginon'
		self.camera_settings = self._getConfigObject(self.vp1.Configuration)

	def setConfig(self, **kwargs):
		'''
		Set commera settings.
		exposure is the exposure time in seconds
		dimension is after binning

		'''
		try:
			if 'exposure' in kwargs:
				exposure = kwargs['exposure']
				self.vp1.ExposureTime = exposure
			if 'binning' in kwargs:
				binning = kwargs['binning']
				# binning can only be set by supported binning objects
				b_index = self.binning_limits.index(binning['x'])
				self.camera_settings.BinningX = self.binning_limits[b_index]
				b_index = self.binning_limits.index(binning['y'])
				self.camera_settings.BinningY = self.binning_limits[b_index]
			if 'dimension' in kwargs:
				dimension = kwargs['dimension']
				self.camera_settings.DimensionX = dimension['x']
				self.camera_settings.DimensionY = dimension['y']
			if 'unbinoff' in kwargs:
				offset = kwargs['unbinoff']
				self.camera_settings.CCDOffsetX = offset['x']
				self.camera_settings.CCDOffsetY = offset['y']
		except:
			raise
		self.camera_settings.FlatMode=0

	def _getConfig(self, param):
		if param == 'binning':
			return {'x':self.camera_settings.BinningX,'y':self.camera_settings.BinningY}
		elif param == 'exposure':
		
			return self.vp1.ExposureTime

	def getExposureTypes(self):
		return ['normal', 'dark']

	def getExposureType(self):
		return self.exposuretype

	def setExposureType(self, value):
		if value not in ['normal', 'dark']:
			raise ValueError('invalid exposure type')
		self.exposuretype = value

	def getPixelSize(self):
		return self.getTvipsConfig('sensor','pixelsize_um')

	def finalizeSetup(self):
		# final bin
		binning = self.binning
		dimension = self.dimension

		# final range
		unbinoff = {'x':self.offset['x']*binning['x'], 'y':self.offset['y']*binning['y']}
		# tvips set exposure in ms
		exposure = int(self.exposure)

		# send it to camera
		self.setConfig(binning= binning, unbinoff=unbinoff, exposure=exposure,dimension=dimension)

	def custom_setup(self):
		'''
		Camrea specific setup
		'''
		pass

	def imageSetup(self):
		self.camera_settings.UseRollingShutter=False
		self.camera_settings.SeriesNumberOfImages=1

	def setNumberOfFrames(self, value):
		self.nframes = int(value)

	def getNumberOfFrames(self):
		return self.nframes

	def movieSetup(self):
		self.camera_settings.UseRollingShutter=True
		self.camera_settings.SeriesNumberOfImages=self.getNumberOfFrames() 

	def getImage(self):
		# The following is copied from ccdcamera.CCDCamera since
		# super (or self.as_super as used in de.py) does not work in proxy call
		if self.readoutcallback:
			name = str(time.time())
			self.registerCallback(name, self.readoutcallback)
			self.backgroundReadout(name)
		else:
			result=self._getImage()
			return result

	def _getImage(self):
		'''
		Acquire an image using the setup for this client.
		'''
		try:
			self.imageSetup()
			self.finalizeSetup()
			self.custom_setup()
			# configurations must be updated with these settings.
			self.instr.CameraConfigurations.Update()
			print('configurations updated')
		except Exception, e:
			if self.getDebugCamera():
				print 'Camera setup',e
			raise RuntimeError('Error setting camera parameters: %s' % (e,))

		t0 = time.time()

		if self.getDebugCamera():
			print 'done waiting before acquire'
		retry = False
		reason = ''
		try:
			self.vp1.AcquireImage()
			im = self.instr.EMImages.Item(1)
			t1 = time.time()
			self.exposure_timestamp = (t1 + t0) / 2.0
		except Exception, e:
			if self.getDebugCamera():
				print 'Camera acquire:',e
				print self.camera_settings.ExposureTime
			raise RuntimeError('Error camera acquiring: %s' % (e,))
		try:
			arr = numpy.array(im.GetDataConvertedAsLong())
		except Exception, e:
			if self.getDebugCamera():
				print 'Camera array:',e
			raise RuntimeError('Camera Error in getting array: %s' % (e,))
		if self.getDebugCamera():
			print 'got arr and to modify'
		arr = self.modifyImage(arr)
		return arr

	def modifyImage(self, arr):
		# transpose
		return numpy.transpose(arr)

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
		return False

	def getInserted(self):
		if self.getRetractable():
			raise NotImplementedError()
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

	def getRecorderFilename(self):
		return self.getTvipsConfig('recorder','default_filename')
	
	def getRecorderDir(self):
		return self.getTvipsConfig('recorder','directory')

	def startMovie(self, filename, exposure_time_ms):
		if self.binning['x'] < 2 or self.dimension['x'] > self.getCameraSize()['x'] / 2.0:
			self.movie_aborted = True
			raise ValueError('Camera binning or dimension too large for movie collection')
		exposure_time_s = exposure_time_ms/1000.0
		try:
			self.movieSetup()
			self.finalizeSetup()
			self.custom_setup()
			# configurations must be updated with these settings.
			self.instr.CameraConfigurations.Update()
		except Exception, e:
			self.movie_aborted = True
			if self.getDebugCamera():
				print 'Camera setup',e
			raise RuntimeError('Error setting camera parameters: %s' % (e,))
		recorder_path = os.path.join(self.getRecorderDir(),self.getRecorderFilename())
		if os.path.isfile(recorder_path):
			os.remove(recorder_path)
		self.vp1.StartContinuous()
		self.vp1.StartRecorder()
		self.movie_aborted = False

	def stopMovie(self, filename, exposure_time_ms):
		if self.movie_aborted:
			return
		exposure_time_s = exposure_time_ms/1000.0
		self.vp1.StopRecorder()
		self.vp1.StopContinuous()
		recorder_path = os.path.join(self.getRecorderDir(),self.getRecorderFilename())
		files = glob.glob(recorder_path+'*.tvips')
		# move Image*.tvips files into taret_code directory
		self.target_code = filename.split('.')[0]
		new_path = os.path.join(self.getRecorderDir(),self.target_code)
		os.mkdir(new_path)
		for f in files:
			shutil.move(f,new_path)
		self.series_length = tvips.readHeaderFromFile(new_path)
		print 'movie name: %s' % filename

class EmMenuXF416E_GPU(EmMenuF416):
	name = 'TVIPS-XF416'
	camera_name = 'TietzXF416E_GPU'
	intensity_averaged = False
	binning_limits = [1,2,4]

class EmMenuF216(EmMenuF416):
	name = 'TVIPS-F216'
	camera_name = 'TietzF216'
	intensity_averaged = False
	binning_limits = [1,2,4]
