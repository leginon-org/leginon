#
# COPYRIGHT:
#	   The Leginon software is Copyright under
#	   Apache License, Version 2.0
#	   For terms of the license agreement
#	   see  http://leginon.org
#

# target intensity:  140410.1

import ccdcamera
import sys
import time
import numpy
import itertools
import os
from pyami import moduleconfig
import numextension

simulation = False
if simulation:
	print 'USING SIMULATION SETTINGS'
	import simgatan
	logdir = os.getcwd()
else:
	import gatansocket
	# on Windows
	logdir = os.path.join(os.environ['USERPROFILE'],'Documents','myami_log')
	if not os.path.isdir(logdir):
		os.mkdir(logdir)

def imagefun_bin(image, binning0, binning1=0):
	'''
	Binning using numextension as implemented in pyami/imagefun.
	bin function in pyami/imagefun.py is copied here so
	that we don't have to import other unnecessary modules
	'''
	if binning1 == 0:
		binning1 = binning0
	if binning0==1 and binning1==1:
		return image
	return numextension.bin(image, binning0, binning1)

# only one connection will be shared among all classes
def connect():
	if not hasattr(gatansocket, 'myGS'):
		gatansocket.myGS = gatansocket.GatanSocket()
	return gatansocket.myGS

def simconnect():
	return simgatan.SimGatan()

configs = moduleconfig.getConfigured('dmsem.cfg')

if 'save_log' in configs['logger'].keys() and configs['logger']['save_log'] is True:
	logfile = os.path.join(logdir,time.strftime('%Y-%m-%d_%H_%M', time.localtime(time.time()))+'.log')
	f=open(logfile,'w')
	f.write('framename\ttime_delta\n')
	f.close()

class DMSEM(ccdcamera.CCDCamera):
	ed_mode = None
	config_opt_name = 'dm'
	filter_method_names = [
			'getEnergyFilter',
			'setEnergyFilter',
			'getEnergyFilterWidth',
			'setEnergyFilterWidth',
			'alignEnergyFilterZeroLossPeak',
		]

	def __init__(self):
		self.unsupported = []
		if not simulation:
			self.camera = connect()
		else:
			self.camera = simconnect()

		self.idcounter = itertools.cycle(range(100))

		ccdcamera.CCDCamera.__init__(self)

		if not self.getEnergyFiltered():
			self.unsupported.extend(self.filter_method_names)
		self.binning = {'x': 1, 'y': 1}
		self.offset = {'x': 0, 'y': 0}
		self.acqoffset = {'x': 0, 'y': 0}
		self.camsize = self.getCameraSize()
		self.dimension = {'x': self.camsize['x'], 'y': self.camsize['y']}
		self.exposuretype = 'normal'
		self.user_exposure_ms = 100
		self.float_scale = 1000.0
		# shutter control
		self.shutter_id = self.getAcquisitionShutter()
		# TODO: semccd command SetShutterNormallyClosed also opens
		# all other shutters.  If these are not set quite right,
		# it can cause trouble. (Found in one case this other shuter
		# uses reverse logic.
		#self.camera.SetShutterNormallyClosed(self.cameraid,self.shutter_id)
		#
		# what to do in digital micrograph before handing back the image
		# unprocessed, dark subtracted, gain normalized
		#self.dm_processing = 'gain normalized'
		self.dm_processing = 'unprocessed'
		self.save_frames = False
		self.frames_name = None
		#self.frame_rate = 4.0
		self.dosefrac_frame_time = 0.200
		self.record_precision = 0.100
		self.readout_delay_ms = 0
		self.align_frames = False
		self.align_filter = 'None'
		self.use_cds = False
		raw_frame_dir = self.getDmsemConfig('k2','raw_frame_dir')
		self.info_print('Frames are saved to %s' % (raw_frame_dir,))

	def __getattribute__(self, attr_name):
		if attr_name in object.__getattribute__(self, 'unsupported'):
			raise AttributeError('attribute not supported')
		return object.__getattribute__(self, attr_name)

	def getDmsemConfig(self,optionname,itemname=None):
		if optionname not in configs.keys():
			return None
		if itemname is None:
			return configs[optionname]
		else:
			if itemname not in configs[optionname]:
				return None
			return configs[optionname][itemname]

	def writeLog(self,line):
		if not self.getDmsemConfig('logger', 'save_log'):
			return
		if logfile and os.path.isfile(logfile):
			f = open(logfile,'a')
			f.write(line)
			f.close()
	def info_print(self, msg):
		v = self.getDmsemConfig('logger', 'verbosity')
		if v is None or v > 0:
			print msg

	def debug_print(self, msg):
		v = self.getDmsemConfig('logger', 'verbosity')
		if v is not None and v > 1:
			print msg

	def getOffset(self):
		return dict(self.offset)

	def setOffset(self, value):
		# Work around
		self.offset = dict(value)

	def getDimension(self):
		return dict(self.dimension)

	def setDimension(self, value):
		# Work around
		self.dimension = dict(value)

	def getBinning(self):
		return dict(self.binning)

	def setBinning(self, value):
		if value['x'] != value['y']:
			raise ValueError('multiple binning dimensions not supported')
		self.binning = dict(value)

	def getRealExposureTime(self):
		return self.getExposureTime() / 1000.0

	def getExposureTime(self):
		return self.user_exposure_ms

	def setExposureTime(self, value):
		self.user_exposure_ms = value

	def getExposureTypes(self):
		return ['normal', 'dark']

	def getExposureType(self):
		return self.exposuretype

	def setExposureType(self, value):
		if value not in ['normal', 'dark']:
			raise ValueError('invalid exposure type')
		self.exposuretype = value

	def isDM230orUp(self):
		version_id,version_string = self.getDMVersion()
		if version_id and version_id >= 40300:
			return True
		return False

	def isDM231orUp(self):
		version_id,version_string = self.getDMVersion()
		if version_id and version_id >= 40301:
			return True
		return False

	def isDM332orUp(self):
		version_id,version_string = self.getDMVersion()
		if version_id and version_id >= 50302:
			return True
		return False

	def isSEMCCD2019orUp(self):
		year = self.getDmsemConfig('semccd',itemname='semccd_plugin_year')
		if year:
			return int(year) >= 2019
		# default to false for back compatibility
		return False

	def getFrameSavingRotateFlipDefault(self):
		'''
		SEMCCD has always default this to 0 until sometime in May 2019.  Users reported that
		the orientation changed on K2 installation with GMS 2.
		'''
		return int(self.isSEMCCD2019orUp())

	def getAcquisitionShutter(self):
		number = self.getDmsemConfig(self.config_opt_name,itemname='acquisition_shutter_number')
		if number is None or number == 1:
			shutter_id = 0
		else:
			shutter_id = 1
		return shutter_id

	def needConfigDimensionFlip(self,height,width):
		# DM 2.3.0 and up needs camera dimension input in its original
		# orientation regardless of rotation when dose fractionation is used.
		if self.isDM230orUp() and (self.save_frames or self.align_frames):
			if height > width:
				return True

		return False

	def _getAcqBinning(self):
		'''
		Camera binning given for acquisition is based on physical pixel,
		regardless of ed mode usually.
		'''
		physical_binning = self.binning['x']
		if self.ed_mode != 'super resolution':
			binscale = 1
		else:
			binscale = 2
			if self.binning['x'] > 1:
				# physical binning is half super resolution binning except when the latter is 1
				physical_binning /= binscale
		return physical_binning, binscale

	def _getAcqDimension(self, acq_binning, binscale):
		acq_dimension = self.camsize.copy()
		physical_binning = binscale * acq_binning
		acq_dimension['x'] = acq_dimension['x']/physical_binning
		acq_dimension['y'] = acq_dimension['y']/physical_binning
		return acq_dimension

	def _getAcqOffset(self, acq_binning, binscale):
		# all software offset for now
		acq_offset = self.acqoffset.copy()
		return acq_offset

	def _getAcqBinningAndROI(self):
		'''
		Calculating the acquisition boundary and binning to send
		to Gatan socket.
		'''
		acq_binning, binscale = self._getAcqBinning()
		acq_dimension = self._getAcqDimension(acq_binning,binscale)
		acq_offset = self._getAcqOffset(acq_binning,binscale)
		height = acq_offset['y']+acq_dimension['y']
		width = acq_offset['x']+acq_dimension['x']
		if self.needConfigDimensionFlip(height,width):
			tmpheight = height
			height = width
			width = tmpheight
		left = acq_offset['x']
		top = acq_offset['y']
		bottom = top + height
		right = left + width
		return acq_binning, left, top, right, bottom, width, height

	def calculateAcquireParams(self):
		'''
		Return acquisition parameters to be sent.
		'''
		exptype = self.getExposureType()
		if exptype == 'dark':
			processing = 'dark'
		else:
			processing = self.dm_processing

		# I think it's negative...
		shutter_delay = -self.readout_delay_ms / 1000.0

		acq_binning, left, top, right, bottom, width, height = self._getAcqBinningAndROI()
		correction_flags = self.getCorrectionFlags()

		acqparams = {
			'processing': processing,
			'height': height,
			'width': width,
			'binning': acq_binning,
			'top': top,
			'left': left,
			'bottom': bottom,
			'right': right,
			'exposure': self.getRealExposureTime(),
			'corrections': correction_flags,
			'shutter': self.shutter_id,
			'shutterDelay': shutter_delay,
		}
		self.debug_print('DM acqire shape (%d, %d)' % (height,width))
		return acqparams

	def custom_setup(self):
		# required for non-K2 cameras
		self.camera.SetReadMode(-1)

	def midNightDelay(self):
		delay_start = self.getDmsemConfig('timing','delay_start_minutes_before_midnight')
		delay_length = self.getDmsemConfig('timing','delay_length_minutes')
		# Check and insert the camera every 0.5 minutes
		self._midNightDelay(delay_start, delay_length, force_insert=0.5)

	def _getImage(self):
		self.midNightDelay()
		self.camera.SelectCamera(self.cameraid)
		self.custom_setup()
		acqparams = self.calculateAcquireParams()
		self.acqparams = acqparams
		t0 = time.time()
		image = self.camera.GetImage(**acqparams)
		t1 = time.time()
		self.exposure_timestamp = (t1 + t0) / 2.0

		if self.getExposureType() == 'dark':
			self.modifyDarkImage(image)
		# workaround dose fractionation image rotate-flip not applied problem
		self.debug_print('received shape %s' %(image.shape,))

		if self.save_frames or self.align_frames:
			if self.save8x8:
                                dec=4 # decimation value : decimate image to 1k x 1.4k for faster stat calculation
                                if image.size > 23569920:  # counted size for k3
                                    dec=8
                                decimated_image = image[::dec,::dec]
				if not self.getDoEarlyReturn():
					#fake 8x8 image with the same mean and standard deviation for fast transfer
				        fake_image = self.base_fake_image*decimated_image.std() + decimated_image.mean()*numpy.ones((8,8))
					return fake_image
				else:
					if self.getEarlyReturnFrameCount() > 0:
						#fake 8x8 image with the same mean and standard deviation for fast transfer
				                fake_image = self.base_fake_image*decimated_image.std() + decimated_image.mean()*numpy.ones((8,8))
					else:
						fake_image = numpy.zeros((8,8))
					self.writeLog('%s\t%.3f\n' % (self.getPreviousRawFramesName(), time.time()-t0))
					return fake_image
			# modify orientation needed only if saving frames
			image = self._modifyImageOrientation(image)
		image = self._modifyImageShape(image)
		self.debug_print('final shape %s' %(image.shape,))

		if self.dm_processing == 'gain normalized' and self.ed_mode in ('counting','super resolution'):
			image = numpy.asarray(image, dtype=numpy.float32)
			image /= self.float_scale
		return image

	def _fixBadShape(self, image):
		# no need to change normally.
		return image

	def _modifyImageShape(self, image):
		image = self._fixBadShape(image)
		acq_binning, binscale = self._getAcqBinning()
		added_binning = self.binning['x'] / acq_binning
		if added_binning > 1:
			# software binning
			image = imagefun_bin(image, added_binning)
			self.debug_print('software binned %s' % (image.shape,))
		image = self._cropImage(image)
		return image

	def _cropImage(self, image):
		# default no modification
		startx = self.getOffset()['x']
		starty = self.getOffset()['y']
		if startx != 0 or starty != 0:
			endx = self.dimension['x'] + startx
			endy = self.dimension['y'] + starty
			image = image[starty:endy,startx:endx]
			self.debug_print('software cropped [%d:%d,%d:%d]' % (starty,endy,startx,endx))
			self.debug_print('software cropped %s' % (image.shape,))
		return image

	def _modifyImageOrientation(self, image):
		if self.isSEMCCD2019orUp() or not self.isDM231orUp():
			k2_rotate = self.getDmsemConfig('k2','rotate')
			k2_flip = self.getDmsemConfig('k2','flip')
			if k2_rotate:
				self.debug_print('rotate image %s' % (image.shape,))
				image = numpy.rot90(image,4-k2_rotate)
			if k2_flip:
				self.debug_print('flip image %s' % (image.shape,))
				image = numpy.fliplr(image)
		return image

	def modifyDarkImage(self,image):
		'''
		in-place modification of image array
		'''
		# non-counting camera default to be as-is.
		return

	def getPixelSize(self):
		## TODO: move to config file:
		# pixel size on Gatan K2
		return {'x': 5e-6, 'y': 5e-6}

	def getRetractable(self):
		return True

	def setInserted(self, value):
		inserted = self.getInserted()
		if not inserted and value:
			self.camera.InsertCamera(self.cameraid, value)
		elif inserted and not value:
			self.camera.InsertCamera(self.cameraid, value)
		else:
			return
		t0=time.time()
		MAX_DELAY = 90 # 90 seconds
		while inserted != value and time.time()-t0 < MAX_DELAY:
			time.sleep(1)
			inserted = self.getInserted()
		if time.time()-t0 >= MAX_DELAY:
			raise RuntimeError('Can not set inserted state of the camera to %s' % (value,))

	def getInserted(self):
		return self.camera.IsCameraInserted(self.cameraid)

	def setReadoutDelay(self, ms):
		if not ms:
			ms = 0
		self.readout_delay_ms = ms

	def getReadoutDelay(self):
		return self.readout_delay_ms

	def getDMVersion(self):
		'''
		version: version_long, major.minor.sub
		'''
		dm_version = self.getDmsemConfig('dm','dm_version')
		if dm_version:
			bits = map((lambda x:int(x)),dm_version.split('.'))
			version_long = (bits[0]+2)*10000 + (bits[1] //10)*100 + bits[1] % 10
		else:
			version_long = self.camera.GetDMVersion()
		if version_long < 40000:
			major = 1
			minor = None
			sub = None
			if version_long >=31100:
				# 2.3.0 gives an odd number of 31100
				major = 2
				minor = 3
				sub = 0
				version_long = 40300
		elif version_long == 40000:
			# minor version can be 0 or 1 in this case
			# but likely 1 since we have not used this module until k2 is around
			major = 2
			minor = 1
			sub = 0
		else:
			major = version_long // 10000 - 2
			remainder = version_long - (major+2) * 10000
			minor = remainder // 100
			sub = remainder % 100
		return (version_long,'%d.%d.%d' % (major,minor,sub))

	def getCorrectionFlags(self):
		'''
		Binnary Correction flag sum in GMS.  See Feature #8391.
		GMS3.3.2 has pre-counting correction which is superior.
		SerialEM always do this correction
		but Leginon 3.4 and earlier does not.
		David M. said SerialEM default is 49 for K2 and 1 for K3.
		49 means defect,bias, and quadrant (to be the same as Ultrascan).
		I don't think the latter two needs applying in counting.
		'''
		if self.isDM332orUp():
			return 1 # defect correction only.
		else:
			# keep it zero to be back compatible.
			return 0

	def hasScriptFunction(self, name):
		return self.camera.hasScriptFunction(name)

	def getEnergyFiltered(self):
		'''
		Return True if energy filter is available through this DM
		'''
		for method_name in self.filter_method_names:
			method_name = method_name[0].upper() + method_name[1:]
			if method_name not in self.camera.filter_functions.keys():
				return False
		return True

	def getEnergyFilter(self):
		'''
		Return True if post column energy filter is enabled
		with slit in
		'''
		return self.camera.GetEnergyFilter() > 0.0

	def setEnergyFilter(self, value):
		'''
		Enable/Disable post column energy filter
		by retracting the slit
		'''
		# setEnergyFilter takes about 1.4 seconds even if in the same state.
		# avoid it to save time.
		if self.getEnergyFilter() == value:
			return
		if value:
			i = 1
		else:
			i = 0
		result = self.camera.SetEnergyFilter(i)
		if result < 0.0:
			raise RuntimeError('unable to set energy filter slit position')

	def getEnergyFilterWidth(self):
		return self.camera.GetEnergyFilterWidth()

	def setEnergyFilterWidth(self, value):
		result = self.camera.SetEnergyFilterWidth(value)
		if result < 0.0:
			raise RuntimeError('unable to set energy filter width')

	def getEnergyFilterOffset(self):
		# get Spectrum Offset in general, but will read Shift gui if
		# set in GMS gui.
		# For example, shift of 10 eV in Quantum LS Control/Main panel gives back -10
		# as the return of this function. Spectrum Offset in the same gui which
		# setEnergyFilterShift affects shows 0 still. After using setEnergyFilterShift function, Shift gui resets to 0.0 while this function reads Spectrum Offset value.
		return self.camera.GetEnergyFilterOffset()

	def setEnergyFilterOffset(self, value):
		# Set Spectrum Offset in Quantum LS Control/Main panel.
		result = self.camera.SetEnergyFilterOffset(value)
		if result < 0.0:
			raise RuntimeError('unable to set energy filter energy shift')

	def alignEnergyFilterZeroLossPeak(self):
		result = self.camera.AlignEnergyFilterZeroLossPeak()
		if result < 0.0:
			raise RuntimeError('unable to align energy filter zero loss peak')

	def setUseCds(self,value):
		self.use_cds = bool(value)

	def getUseCds(self):
		return self.use_cds

class GatanOrius(DMSEM):
	name = 'GatanOrius'
	config_opt_name = 'orius'
	try:
		cameraid = configs[config_opt_name]['camera_id']
	except:
		pass
	binning_limits = [1,2,4]
	binmethod = 'exact'

class GatanUltraScan(DMSEM):
	name = 'GatanUltraScan'
	config_opt_name = 'orius'
	try:
		cameraid = configs[config_opt_name]['camera_id']
	except:
		pass
	binning_limits = [1,2,4,8]
	binmethod = 'exact'

class GatanRio9(DMSEM):
	name = 'GatanRio9'
	config_opt_name = 'rio9'
	try:
		cameraid = configs[config_opt_name]['camera_id']
	except:
		pass
	binning_limits = [1,2]
	binmethod = 'exact'

	def getPixelSize(self):
		## TODO: move to config file:
		return {'x': 9e-6, 'y': 9e-6}


class GatanK2Base(DMSEM):
	name = 'GatanK2Base'
	config_opt_name = 'k2'
	try:
		cameraid = configs[config_opt_name]['camera_id']
	except:
		raise
		pass
	# our name mapped to SerialEM plugin value
	readmodes = {'linear': 0, 'counting': 1, 'super resolution': 2}
	ed_mode = 'base'
	hw_proc = 'none'
	binning_limits = [1,2,4,8]
	binmethod = 'floor'
	filePerImage = False

	k2_max_ram_for_stack_gb = 12 # maximal ram for ram grabs
	# base fake image of 8x8 shape, mean=0,0 and std=1.0
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
		super(GatanK2Base, self).__init__()
		self.frame_name_prefix = self.getFrameNamePrefix()
		# set default return frame count.
		self.setEarlyReturnFrameCount(None)
		self.save8x8 = False

	def getFrameNamePrefix(self):
		prefix = self.getDmsemConfig('k2','frame_name_prefix')
		if prefix is None:
			prefix = ''
		return prefix

	def custom_setup(self):
		'''
		K2 specific setup.
		'''
		#self.camera.SetShutterNormallyClosed(self.cameraid,self.bblankerid)
		if self.ed_mode != 'base':
			k2params = self.calculateK2Params()
			self.camera.SetK2Parameters(**k2params)
			fileparams = self.calculateFileSavingParams()
			if fileparams['rootname'] != 'dummy':
				self.debug_print('FILESAVING %s %s' % (fileparams['dirname'],fileparams['rootname']))
			self.camera.SetupFileSaving(**fileparams)

	def getFrameTime(self):
		ms = self.dosefrac_frame_time * 1000.0
		return ms

	def setFrameTime(self,ms):
		seconds = ms / 1000.0
		self.dosefrac_frame_time = seconds

	def getExposurePrecision(self):
		if self.isDoseFracOn():
			frame_time = self.dosefrac_frame_time
		else:
			frame_time = self.record_precision
		return frame_time

	def getRealExposureTime(self):
		'''
		The real exposure time is rounded to the nearest
		"exposure precision unit" in seconds, but not less than one "unit"
		'''
		precision = self.getExposurePrecision()
		user_time = self.user_exposure_ms / 1000.0
		if user_time < precision:
			real_time = precision
		else:
			real_time = round(user_time / precision) * precision
		return real_time

	def getExposureTime(self):
		real_time = self.getRealExposureTime()
		real_time_ms = int(round(real_time * 1000))
		return real_time_ms

	# our name mapped to SerialEM plugin value
	hardwareProc = {'none': 0, 'dark': 2, 'gain': 4, 'dark+gain': 6}

	def isDoseFracOn(self):
		return self.save_frames or self.align_frames

	def getFastSave(self):
		# Fastsave saves a small image arrary for frame camera to reduce handling time.
		return self.save8x8

	def setFastSave(self, state):
		# Fastsave saves a smaller image arrary for frame camera to reduce handling time.
		self.save8x8 = state

	def calculateK2Params(self):
		frame_time = self.dosefrac_frame_time
		params = {
			'readMode': self.readmodes[self.ed_mode],
			#'scaling': self.float_scale,
			'scaling': 1.0,
			'hardwareProc': self.hardwareProc[self.hw_proc],
			'doseFrac': self.isDoseFracOn(),
			'frameTime': frame_time,
			'alignFrames': self.align_frames,
			'saveFrames': self.save_frames,
			'filt': self.align_filter,
			'useCds': self.use_cds,
		}
		return params

	def calculateFileSavingParams(self):
		'''
		Creates raw frame file saving parameters independent of
		the integrated image returned to Leginon
		'''
		if self.isDoseFracOn():
			# This makes it always take the value in dmsem.cfg
			self.setEarlyReturnFrameCount(None)
			prefix = self.frame_name_prefix
			frames_name = time.strftime('%Y%m%d_%H%M%S', time.localtime())
			self.frames_name = prefix + frames_name + '%02d' % (self.idcounter.next(),)
		else:
			self.frames_name = 'dummy'
		raw_frame_dir = self.getDmsemConfig('k2','raw_frame_dir')
		if self.filePerImage:
			path = raw_frame_dir + self.frames_name
			fileroot = 'frame'
		else:
			path = raw_frame_dir 
			fileroot = self.frames_name

		# 0 means takes what DM gives
		rot_flip = self.getFrameSavingRotateFlipDefault()
		if not self.isDM231orUp():
			# Backward compatibility
			flip = int(not self.getDmsemConfig('k2','flip'))*4  # 0=none, 4=flip columns before rot, 8=flip after
			rot_flip = self.getDmsemConfig('k2','rotate') + flip

		params = {
			'rotationFlip': rot_flip,
			'dirname': path,
			'rootname': fileroot,
			'filePerImage': self.filePerImage,
			'doEarlyReturn': self.getDoEarlyReturn(),
			'earlyReturnFrameCount': self.getEarlyReturnFrameCount(),
			'earlyReturnRamGrabs': self.getEarlyReturnRamGrabs(),
			'lzwtiff': self.getSaveLzwTiffFrames(),
		}
		return params

	def getEarlyReturnRamGrabs(self):
		if not self.getDoEarlyReturn() or not self.isDM231orUp():
			return 0
		# For DM2.3.1 and up, need to grab frames in ram before return
		nframes = self.getNumberOfFrames()
		maxMemory = self.k2_max_ram_for_stack_gb * (1024**3)
		pixels = self.dimension['x']*self.dimension['y']*self.binning['x']*self.binning['y']
		max_ram_frames = maxMemory // pixels
		# Grab up to the maximal ram available for the purpose.
		# The rest will need to be dumped to disk before another image is taken.
		return min(nframes, max_ram_frames)
			
	def getEarlyReturnFrameCount(self):
		return self.early_return_frame_count

	def setEarlyReturnFrameCount(self, value=None):
		nframes = self.getNumberOfFrames()
		if type(value) is type(1):
			# Mainly for testing
			self.early_return_frame_count = min([value, nframes])
		else:
			# Read from dmsem.cfg
			self.early_return_frame_count = min([self.getDmsemConfig('k2','early_return_frame_count'), nframes])

	def getDoEarlyReturn(self):
		return bool(self.getDmsemConfig('k2','do_early_return'))

	def getSaveLzwTiffFrames(self):
		return bool(self.getDmsemConfig('k2','save_lzw_tiff_frames'))

	def setAlignFrames(self, value):
		self.align_frames = bool(value)

	def getAlignFrames(self):
		return self.align_frames

	def setAlignFilter(self, value):
		self.align_filter = str(value)

	def getAlignFilter(self):
		return self.align_filter

	def getSaveRawFrames(self):
		return self.save_frames

	def setSaveRawFrames(self, value):
		self.save_frames = bool(value)

	def getPreviousRawFramesName(self):
		return self.frames_name

	def getNumberOfFrames(self):
		frame_time = self.dosefrac_frame_time
		real_time = self.getRealExposureTime()
		nframes = int(round(real_time / frame_time))
		return nframes

	def getNumberOfFramesSaved(self):
		if self.save_frames:
			return self.getNumberOfFrames()
		else:
			return 0

	def setUseFrames(self, frames):
		pass

	def getUseFrames(self):
		nframes = self.getNumberOfFrames()
		return tuple(range(nframes))

	def getFrameFlip(self):
		'''
		Frame flip saved in CameraEMData for frame alignment
		software.  Frame Flip is defined as up-down flip
		'''
		overwrite = self.getDmsemConfig('k2','overwrite_frame_orientation')
		if not overwrite:
			return self.isDM231orUp()
		else:
			my_frame_flip = self.getDmsemConfig('k2','frame_flip_to_overwrite_with')
			return my_frame_flip

	def getFrameRotate(self):
		'''
		Frame Rotate direction is defined as x to -y rotation applied after up-down flip
		'''
		return 0

	def updateDarkCurrentReference(self):
		r = self.camera.UpdateK2HardwareDarkReference(self.cameraid)
		if r > 0:
			# has error
			return True
		return False

	def requireRecentDarkCurrentReferenceOnBright(self):
		return True

class GatanK2Linear(GatanK2Base):
	name = 'GatanK2Linear'
	ed_mode = 'linear'
	hw_proc = 'none'

class GatanK2Counting(GatanK2Base):
	logged_methods_on = True
	name = 'GatanK2Counting'
	ed_mode = 'counting'
	if simulation:
		hw_proc = 'none'
	else:
		hw_proc = 'dark+gain'

	def getSystemDarkSubtracted(self):
		return True

	def modifyDarkImage(self,image):
		'''
		in-place modification of image array
		'''
		if self.isDM231orUp():
			image[:,:] = 0

class GatanK2Super(GatanK2Base):
	name = 'GatanK2Super'
	ed_mode = 'super resolution'
	binning_limits = [1]
	binmethod = 'floor'
	if simulation:
		hw_proc = 'none'
	else:
		hw_proc = 'dark+gain'

	def calculateAcquireParams(self):
		'''
		Return K2 super resolution acquisition parameters to be sent.
		Super resolution camera need to send camera boundary in physical size
		but ask for an image at super resolution size.
		'''
		acqparams = super(GatanK2Super,self).calculateAcquireParams()
		# K2 SerialEMCCD native is in counting
		acq_binning, binscale = self._getAcqBinning()
		acqparams['height'] *= binscale
		acqparams['width'] *= binscale
		return acqparams

	def modifyDarkImage(self,image):
		'''
		in-place modification of image array
		'''
		if self.isDM231orUp():
			image[:,:] = 0

	def getPixelSize(self):
		## TODO: move to config file:
		# pixel size on Gatan K2
		return {'x': 2.5e-6, 'y': 2.5e-6}

class GatanK3(GatanK2Base):
	# K3 camsize is in super resolution
	binning_limits = [1,2,4,8]
	soft_crop = True
	name = 'GatanK3'
	config_opt_name = 'k3'
	try:
		# Not yet transition to always use k3
		cameraid = configs[config_opt_name]['camera_id']
		if cameraid is None:
			cameraid = configs['k2']['camera_id']
	except:
		pass
	readmodes = {'linear': 3, 'super resolution': 4}
	ed_mode = 'super resolution'
	if simulation:
		hw_proc = 'none'
	else:
		hw_proc = 'dark+gain'

	def __init__(self):
		super(GatanK3, self).__init__()
		self.dosefrac_frame_time = 0.013
		self.record_precision = 0.013
		self.user_exposure_ms = 13
		self.use_cds = False
		self.dm_processing = self.getDmProcessing()

	def getDmProcessing(self):
		value = self.getDmsemConfig('k3','dm_processing')
		if value == 'dark subtracted':
			return value
		else:
			# default
			return 'gain normalized'

	def getSystemGainDarkCorrected(self):
		# deprecated in v3.6
		return self.dm_processing == 'gain normalized'

	def getSystemDarkSubtracted(self):
		return self.dm_processing in ('dark subtracted', 'gain normalized')

	def getFrameGainCorrected(self):
		return self.dm_processing == 'gain normalized'

	def getSumGainCorrected(self):
		return self.dm_processing == 'gain normalized'

	def requireRecentDarkCurrentReferenceOnBright(self):
		return True

	def updateDarkCurrentReference(self):
		r = self.camera.PrepareDarkReference(self.cameraid)
		if r > 0:
			# has error
			return True
		return False

	def getFrameFlip(self):
		'''
		Frame flip saved in CameraEMData for frame alignment
		software.  Frame Flip is defined as up-down flip
		K3 requires no flip in most cases.
		'''
		overwrite = self.getDmsemConfig('k2','overwrite_frame_orientation')
		if not overwrite:
			return False
		else:
			my_frame_flip = self.getDmsemConfig('k2','frame_flip_to_overwrite_with')
			return my_frame_flip

	def getFrameSavingRotateFlipDefault(self):
		'''
		SEMCCD has always default this to 0 until sometime in May 2019.  Users reported that
		the orientation changed on K2 installation with GMS 2 but seems to be back to normal
		on K3 installations.
		'''
		# rotation is built-in.  no need to set.
		gms_flip = self.getDmsemConfig('k2','flip')
		# Not sure why it needs to be done this way.  Most likely because
		# mrc file in SerialEM is oriented so that the origin
		# is at bottom-left corner.
		if gms_flip:
			return 0
		return 4

	def _getAcqBinning(self):
		# K3 SerialEMCCD native is in super resolution
		acq_binning = self.binning['x']
		if self.binning['x'] > 2:
			#K3 can only bin from super resolution by 1 or 2.
			acq_binning = 2
		# bin scale is always 1
		return acq_binning, 1

	def modifyDarkImage(self,image):
		image[:,:] = 0

	def _fixBadShape(self, image):
		# TODO: Found image shape returned incorrectly in simulation.
		# Leave this here for now.
		if self.acqparams['width']*self.acqparams['height'] != image.shape[0]*image.shape[1]:
			print 'ERROR: image not in the right shape'
			return image
		else:
			# simulator binned image when saving frames has wrong shape
			if self.acqparams['width'] != image.shape[1]:
				image = image.reshape(self.acqparams['height'],self.acqparams['width'])
				print 'WARNING: image reshaped', image.shape
		return image

	def getPixelSize(self):
		# pixel size on Gatan K3 as super resolution.  TODO: need confirmation.
		return {'x': 2.5e-6, 'y': 2.5e-6}

