import copy
import ccdcamera
import numpy
from scipy import ndimage
import random
random.seed()
import time
import math
import json
import remote
import os
import glob
import threading
import shutil

from pyami import mrc, imagefun, numpil
import itertools
from pyscope import falconframe

DEBUG = False
FRAME_DIR = '.'
START_TIME = 11*60+16
rawtype = numpy.uint32
frametype = numpy.uint8
idcounter = itertools.cycle(range(100))

has_energy_filter = True

class SimCCDCamera(ccdcamera.CCDCamera):
	name = 'SimCCDCamera'
	binning_limits = [1,2,4,8]
	binmethod = 'exact'

	def __init__(self):
		self.unsupported = []
		super(SimCCDCamera,self).__init__()
		self.debug = DEBUG
		self.pixel_size = {'x': 1.4e-5, 'y': 1.4e-5}
		self.exposure_types = ['normal', 'dark', 'bias']

		self.binning = {'x': 1, 'y': 1}
		self.offset = {'x': 0, 'y': 0}
		self.dimension = copy.copy(self.getCameraSize())
		self.exposure_time = 0.2
		self.exposure_type = 'normal'

		self.energy_filter = True
		self.energy_filter_width = 20.0

		self.views = ('square', 'empty')
		self.view = 'square'
		#self.view = 'empty'
		self.inserted = True
		if not has_energy_filter:
			self.unsupported = [
					'getEnergyFilter',
					'setEnergyFilter',
					'getEnergyFilterWidth',
					'setEnergyFilterWidth',
					'alignEnergyFilterZeroLossPeak',
			]
		if 'simpar' in self.conf and self.conf['simpar'] and os.path.isdir(self.conf['simpar']):
			self.simpar_dir = self.conf['simpar']
		else:
			self.simpar_dir = None
		self.current_image_count = {}

	def __getattribute__(self, attr_name):
		if attr_name in object.__getattribute__(self, 'unsupported'):
			raise AttributeError('attribute not supported')
		return object.__getattribute__(self, attr_name)

	def getSystemGainDarkCorrected(self):
		# deprecated in v3.6
		return self.getSumGainCorrected()

	def getSystemDarkSubtracted(self):
		# Default to not do dark subtraction if have simulated images
		if self.simpar_dir is None:
			return False
		else:
			return True

	def getSumGainCorrected(self):
		# Default to not do gain correction if have simulated images
		if self.simpar_dir is None:
			return False
		else:
			return True

	def getFrameGainCorrected(self):
		# frames don't use simpar
		return False

	def getRetractable(self):
		return True

	def getInserted(self):
		return self.inserted

	def setInserted(self, value):
		self.inserted = value

	def setView(self, view):
		self.view = view

	def getView(self):
		return self.view

	def getViews(self):
		return self.views

	def getBinnedMultiplier(self):
		binning = self.getBinning()
		return binning['x']*binning['y']

	def getBinning(self):
		return copy.copy(self.binning)

	def setBinning(self, value):
		for axis in self.binning.keys():
			try:
				if value[axis] not in self.getCameraBinnings():
					raise ValueError('invalid binning')
			except KeyError:
				pass

		for axis in self.binning.keys():
			try:
				self.binning[axis] = value[axis]
			except KeyError:
				pass

	def getOffset(self):
		return copy.copy(self.offset)

	def setOffset(self, value):
		for axis in self.offset.keys():
			try:
				if value[axis] < 0 or value[axis] >= self.getCameraSize()[axis]:
					raise ValueError('invalid offset')
			except KeyError:
				pass

		for axis in self.offset.keys():
			try:
				self.offset[axis] = value[axis]
			except KeyError:
				pass

	def getDimension(self):
		return copy.copy(self.dimension)

	def setDimension(self, value):
		for axis in self.dimension.keys():
			try:
				if value[axis] < 1 or value[axis] > self.getCameraSize()[axis]:
					raise ValueError('invalid dimension')
			except KeyError:
				pass

		for axis in self.dimension.keys():
			try:
				self.dimension[axis] = value[axis]
			except KeyError:
				pass

	def getExposureTime(self):
		return self.exposure_time*1000.0

	def setExposureTime(self, value):
		if value < 0:
			raise ValueError('invalid exposure time')
		self.exposure_time = value/1000.0

	def getExposureTypes(self):
		return self.exposure_types

	def getExposureType(self):
		return self.exposure_type

	def setExposureType(self, value):
		if value not in self.exposure_types:
			raise ValueError('invalid exposure type')
		self.exposure_type = value

	def _getImage(self):
		if not self.validateGeometry():
			raise ValueError('invalid image geometry')

		for axis in ['x', 'y']:
			if self.dimension[axis] * self.binning[axis] > self.getCameraSize()[axis]:
				raise ValueError('invalid dimension/binning combination')

		columns = self.dimension['x']
		rows = self.dimension['y']

		shape = (rows, columns)

		t0 = time.time()
		## exposure time
		time.sleep(self.exposure_time)
		t1 = time.time()
		self.exposure_timestamp = (t1 + t0) / 2.0
		return self.getSimImage(shape)

	def getSimImage(self,shape):
		if not self.simpar_dir or self.exposure_type == 'dark':
			return self.getSyntheticImage(shape)
		else:
			return self.getSimParImage(shape)

	def getAllSimPar(self):	
		f = open(os.path.join(self.simpar_dir,'simpar.json'),'r+')
		try:
			all_simpar = json.loads(f.read())
		except ValueError:
			all_simpar = {}
		return all_simpar

	def getSimParImage(self,shape):
		'''
		Return images saved in advanced according to sim tem parameters.
		The jpg images should be use full camera with binning identified
		in the filename such as 'bin4_0.jpg'. '_0' identify the first of
    the number of images the function pulled from iteratively. 
		'''
		all_simpar = self.getAllSimPar()
		if not all_simpar:
			return self.getSyntheticImage(shape)
		mag = int(all_simpar['magnification'])
		mag_str = '%d' % mag
		# images are saved under the magnification value in simpar.json
		files = os.listdir(os.path.join(self.simpar_dir,mag_str))
		required_bin = self.binning['x']
		this_bin_files = []
		for f in files:
			try:
				this_bin = int(f[3])
			except ValueError:
				# ignore those not named as bin*
				continue
			if mag not in self.current_image_count:
				self.current_image_count[mag]={}
			if this_bin not in self.current_image_count[mag]:
				self.current_image_count[mag][this_bin]=-1
			if this_bin == required_bin:
				this_bin_files.append(f)
		mag_dir = os.path.join(self.simpar_dir,mag_str)
		if not this_bin_files:
			return self.getSyntheticImage(shape)
		# Files are not sorted by name in os.listdir
		this_bin_files.sort()
		# Loop through images to load
		self.current_image_count[mag][required_bin] += 1
		if self.current_image_count[mag][required_bin] > len(this_bin_files)-1:
			self.current_image_count[mag] [required_bin]= 0
		this_imagefile = this_bin_files[self.current_image_count[mag][required_bin]]
		image = numpil.read(os.path.join(mag_dir,this_imagefile))
		if len(image.shape) == 3:
			# rgb channels
			image = image.sum(2)
		#corping
		need_padding = False
		if image.shape[0] > shape[0]:
			image = image[self.offset['y']:shape[0]+self.offset['y'],:]
		elif image.shape[0] < shape[0]:
			need_padding = True
		if image.shape[1] > shape[1]:
			image = image[:,self.offset['x']:shape[1]+self.offset['x']]
		elif image.shape[1] < shape[1]:
			need_padding = True
		if need_padding:
			mean = image.mean()
			sigma = image.std()
			off = ((shape[0]-image.shape[0])//2, (shape[1]-image.shape[1])//2)
			new = numpy.random.normal(mean, sigma, shape)
			new[off[0]:off[0]+image.shape[0],off[1]:off[1]+image.shape[1]] = image
			image = new
		return image

	def getSyntheticImage(self,shape):
		dark_mean = 1.0
		bright_scale = 10
		if self.exposure_type != 'dark':
			mean = self.exposure_time * 1000.0 *bright_scale + dark_mean
			sigma = 0.01 * mean
		else:
			mean = dark_mean
			sigma = 0.1 * mean
		image = numpy.random.normal(mean, sigma, shape)
		if self.exposure_type != 'dark':
			row_offset = random.randint(-shape[0]/16, shape[0]/16) + shape[0]/4
			column_offset = random.randint(-shape[1]/16, shape[1]/16) + shape[0]/4
			image[row_offset:row_offset+shape[0]/2,
				column_offset:column_offset+shape[1]/2] += 0.5 * mean
		image = numpy.asarray(image, dtype=numpy.uint16)
		return image

	def getEnergyFiltered(self):
		return has_energy_filter

	def getEnergyFilter(self):
		return self.energy_filter

	def setEnergyFilter(self, value):
		self.energy_filter = bool(value)

	def getEnergyFilterWidth(self):
		return self.energy_filter_width

	def setEnergyFilterWidth(self, value):
		self.energy_filter_width = float(value)

	def alignEnergyFilterZeroLossPeak(self):
		time.sleep(1.0)
		pass

	def getPixelSize(self):
		return dict(self.pixel_size)

	def startMovie(self,filename, exposure_time_ms):
		self.movie_start_time = time.time()

	def stopMovie(self, filename, exposure_time_ms):
		series_length = math.ceil((time.time() -self.movie_start_time)/(0.001*exposure_time_ms))
		self.series_length = 0
		self.target_code = filename.split('.bin')[0]
		t = threading.Thread(target=self._saveMovie, args=[series_length,])
		t.start()
		self._waitForSaveMoveDone()
		self._moveMovie()

	def _moveMovie(self):
		data_dir = './'
		pattern = os.path.join(data_dir, '%s*.bin' % (self.target_code,))
		new_dir = '' # do not move
		if not new_dir:
			return
		if not os.path.isdir(new_dir):
			raise ValueError('TIA exported data network Directory %s is not a directory' % (new_dir,))
		if data_dir == new_dir:
			# nothing to do
			return
		else:
			pattern = os.path.join(data_dir, '%s*.bin' % (self.target_code,))
			files = glob.glob(pattern)
			for f in files:
				shutil.move(f, new_dir)

	def _saveMovie(self, series_length):
		for i in range(int(series_length)):
			frame_path = os.path.join(FRAME_DIR,'%s_%03d.bin' % (self.target_code, i+1))
			f = open(frame_path,'w')
			f.write('data\n')
			f.close()
			time.sleep(0.5)

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

	def _findSeriesLength(self):
		pattern = os.path.join(FRAME_DIR,'%s_*' % (self.target_code,))
		length = len(glob.glob(pattern))
		return length

class SimFrameCamera(SimCCDCamera):
	name = 'SimFrameCamera'
	def __init__(self):
		super(SimFrameCamera,self).__init__()
		self.frame_time = 200
		self.save_frames = False
		self.alignframes = False
		self.alignfilter = 'None'
		self.rawframesname = 'frames'
		self.useframes = ()
		self.save8x8 = False

	def _simBias(self, shape):
		bias = numpy.arange(100,115)
		bias = numpy.resize(bias, shape)
		noise = numpy.random.normal(0.0, 2.0, shape)
		bias = bias + noise
		bias = numpy.asarray(bias, rawtype)
		return bias

	def _simDark(self, shape, exptime):
		# return image:  dark + bias
		## counts per second
		darkrate = numpy.array((0.1, 0.1, 0.1, 0.1, 0.2, 0.2, 0.2, 0.2), numpy.float32)
		dark = exptime * darkrate
		dark = numpy.resize(dark, shape)
		dark = dark + self._simBias(shape)
		dark = numpy.asarray(dark, rawtype)
		self.debug_print( 'DARK %s' % (dark,))
		return dark

	def _simExposure(self, shape, exptime):
		# return image:  dark + bias + exposure
		# light sensitivity in counts per second
		sensitivity = self.binning['x'] * self.binning['y'] * numpy.arange(2000, 2065)
		sensitivity = numpy.resize(sensitivity, shape)
		exposure = exptime * sensitivity
		noise = numpy.random.normal(0.0, 50.0, shape)
		exposure = exposure + noise
		final = self._simDark(shape, exptime) + exposure
		final = numpy.asarray(final, rawtype)
		self.debug_print( 'EXP %s' % (final,))
		return final

	def _simNormal(self, shape, exptime):
		# return image:  transparency * (dark + bias + exposure)
		final = self._simExposure(shape, exptime) * self._simSample(shape)
		final = numpy.asarray(final, rawtype)
		self.debug_print( 'NORMAL %s' % (final,))
		return final

	def _simSample(self, shape):
		if self.view == 'empty':
			transparency = numpy.ones(shape, dtype=numpy.float32)
		elif self.view == 'square':
			transparency = 0.9 * numpy.ones(shape, dtype=numpy.float32)
			row_offset = random.randint(-shape[0]/8, shape[0]/8) + shape[0]/4
			column_offset = random.randint(-shape[1]/8, shape[1]/8) + shape[0]/4
			transparency[row_offset:row_offset+shape[0]/2,
					column_offset:column_offset+shape[1]/2] = 0.7
		return transparency

	def convertToInt8(self,array):
		min = 0
		max = array.max()
		array = (array / (numpy.ones(array.shape)*max))*128
		array = numpy.asarray(array,numpy.int8)
		return array

	def custom_setup(self):
		'''
		Place holder for more setup
		'''
		pass

	def _getImage(self):
		'''
		Set up and get image and frames for frame camera
		'''
		self._midNightDelay(-(START_TIME),0,0)
		self.custom_setup()
		if not self.validateGeometry():
			raise ValueError('invalid image geometry')

		for axis in ['x', 'y']:
			if self.dimension[axis] * self.binning[axis] > self.getCameraSize()[axis]:
				raise ValueError('invalid dimension/binning combination')

		columns = self.dimension['x']
		rows = self.dimension['y']

		shape = (rows, columns)

		t0 = time.time()
		## exposure time
		time.sleep(self.exposure_time)
		t1 = time.time()
		self.exposure_timestamp = (t1 + t0) / 2.0

		nframes = self.getNumberOfFrames()
		exptime = self.frame_time

		if self.useframes:
			useframes = []
			for f in self.useframes:
				if 0 <= f < nframes:
					useframes.append(f)
		else:
			# use all frames in final image
			useframes = range(nframes)
		self.useframes = useframes

		self.debug_print( 'SAVERAWFRAMES %s' % (self.save_frames,))
		if self.save_frames:
			self.rawframesname = time.strftime('frames_%Y%m%d_%H%M%S')
			self.rawframesname += '_%02d' % (idcounter.next(),)
		else:
			return self.getSimImage(shape)
		# won't be here if not saving frames
		sum = numpy.zeros(shape, numpy.float32)

		for i in range(nframes):
			if self.exposure_type == 'bias':
				frame = self._simBias(shape)
			elif self.exposure_type == 'dark':
				frame = self._simDark(shape, exptime)
			elif self.exposure_type == 'normal':
				frame = self._simNormal(shape, exptime)
			else:
				raise RuntimeError('unknown exposure type: %s' % (self.exposure_type,))
			#Keep it small
			frame = self.convertToInt8(frame)
			mrcname = '.mrc'
			fname = os.path.join(FRAME_DIR,self.rawframesname + mrcname)
			if self.save_frames:
				self.debug_print('SAVE %d' %i)
				if i == 0:
					mrc.write(frame, fname)
				else:
					mrc.append(frame, fname)
			if i in self.useframes:
				self.debug_print('PRINT %d' %i)
				sum += frame

		if self.save8x8:
			shape8 = (8,8)
			return self.getSimImage(shape8)
		sleeptime = time.time()-t0
		return sum

	def getFastSave(self):
		# Fastsave saves a smaller image arrary for frame camera to reduce handling time.
		return self.save8x8

	def setFastSave(self, state):
		# Fastsave saves a smaller image arrary for frame camera to reduce handling time.
		self.save8x8 = bool(state)

	
	def getNumberOfFrames(self):
		if self.frame_time:
			nframes = int(round(self.exposure_time / self.frame_time))
			return nframes
		else:
			return 1

	def getFrameTime(self):
		ms = self.frame_time * 1000.0
		return ms

	def setFrameTime(self,ms):
		seconds = ms / 1000.0
		self.frame_time = seconds

	def getSaveRawFrames(self):
		'''Save or Discard'''
		return self.save_frames

	def setSaveRawFrames(self, value):
		'''True: save frames,  False: discard frames'''
		self.save_frames = bool(value)

	def getAlignFrames(self):
		return self.alignframes

	def setAlignFrames(self, value):
		self.alignframes = bool(value)

	def getAlignFilter(self):
		return self.alignfilter

	def setAlignFilter(self, value):
		if value:
			self.alignfilter = str(value)
		else:
			self.alignfilter = 'None'

	def setNextRawFramesName(self, value):
		self.rawframesname = value

	def getNextRawFramesName(self):
		return self.rawframesname

	def getPreviousRawFramesName(self):
		return self.rawframesname

	def setUseFrames(self, value):
		self.useframes = value

	def getUseFrames(self):
		return self.useframes

	def requireRecentDarkCurrentReferenceOnBright(self):
		return False
	
	def updateDarkCurrentReference(self):
		self.debug_print('Fake Dark Current Reference update')
		# no error
		return False

class SimFalconFrameCamera(SimFrameCamera):
	name = 'SimFalconFrameCamera'
	def __init__(self):
		super(SimFalconFrameCamera,self).__init__()
		self.frameconfig = falconframe.FalconFrameConfigXmlMaker(simu=True)
		self.movie_exposure = 500.0
		self.start_frame_number = 1
		self.end_frame_number = 7
		self.equal_distr_frame_number = 0

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
		self.frameconfig.setExposureTime(self.exposure_time)
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
		# self.useframes is used in simulater to generate simulated sum image
		self.useframes = tuple(range(self.start_frame_number-self.frameconfig.internal_readout_delay, self.end_frame_number-self.frameconfig.internal_readout_delay))

	def getUseFrames(self):
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
			self.frameconfig.makeDummyConfig(movie_exposure_second)

class SimOtherCCDCamera(SimCCDCamera):
	name = 'SimOtherCCDCamera'
	def __init__(self):
		super(SimOtherCCDCamera,self).__init__()
		self.binning_limits = [1,2,4,8]
		self.binmethod = 'floor'

	def _getImage(self):
		im = SimCCDCamera._getImage(self)
		im = 10 * im
		return im

class SimCeta(SimCCDCamera):
	name = 'SimCeta'

class SimK2CountingCamera(SimFrameCamera):
	name = 'SimK2CountingCamera'
	def __init__(self):
		super(SimK2CountingCamera,self).__init__()
		self.binning_limits = [1,2,4,8]
		self.binmethod = 'floor'
		self.pixel_size = {'x': 5e-6, 'y': 5e-6}

	def getSystemDarkSubtracted(self):
		return True

	def getFrameFlip(self):
		# flip before? rotation
		return False

	def getFrameRotate(self):
		# rotation in multiple of 90 degrees
		return 0

	def getSystemDarkSubtracted(self):
		return True

	def getFrameGainCorrected(self):
		return False

class SimK2SuperResCamera(SimK2CountingCamera):
	name = 'SimK2SuperResCamera'
	def __init__(self):
		super(SimK2SuperResCamera,self).__init__()
		self.binning_limits = [1]
		self.binmethod = 'floor'
		self.pixel_size = {'x': 2.5e-6, 'y': 2.5e-6}


def imagefun_bin(image, binning0, binning1=0):
	return imagefun.bin(image, binning0)

class SimK3Camera(SimFrameCamera):
	name = 'SimK3Camera'
	def __init__(self):
		super(SimK3Camera,self).__init__()
		self.binning_limits = [1,2,4,8]
		self.binmethod = 'floor'
		self.camsize = self.getCameraSize()
		self.tempoffset = dict(self.offset)
		self.pixel_size = {'x': 2.5e-6, 'y': 2.5e-6}

	def getSystemDarkSubtracted(self):
		return True

	def getFrameGainCorrected(self):
		return False

	def setOffset(self, value):
		# Work around
		self.offset = dict(value)
		self.tempoffset = {'x':0,'y':0}

	def setUseCds(self,value):
		self.use_cds = bool(value)

	def getUseCds(self):
		return self.use_cds

	def _getImage(self):
		if not self.validateGeometry():
			raise ValueError('invalid image geometry')

		for axis in ['x', 'y']:
			if self.dimension[axis] * self.binning[axis] > self.getCameraSize()[axis]:
				raise ValueError('invalid dimension/binning combination')

		acqparams = self.calculateAcquireParams()
		self.acqparams = acqparams

		columns = self.acqparams['width']
		rows = self.acqparams['height']

		shape = (rows, columns)

		t0 = time.time()
		## exposure time
		time.sleep(self.exposure_time)
		t1 = time.time()
		self.exposure_timestamp = (t1 + t0) / 2.0
		image = self.getSimImage(shape)
		image = self._modifyImageShape(image)
		return image
		
	def needConfigDimensionFlip(self, height,width):
		return False

	def calculateAcquireParams(self):
		acq_binning, left, top, right, bottom, width, height = self.getAcqBinningAndROI()
		return {'width':width, 'height':height}

	def getAcqBinning(self):
		self.acq_binning = self.binning['x']
		if self.binning['x'] > 2:
			#K3 can only bin from super resolution by 1 or 2.
			self.acq_binning = 2
		# bin scale is 1 always
		return self.acq_binning, 1

	def getAcqBinningAndROI(self):
		acq_binning, binscale = self.getAcqBinning()
		height = self.camsize['y'] / acq_binning
		width = self.camsize['x'] / acq_binning
		if self.needConfigDimensionFlip(height,width):
			tmpheight = height
			height = width
			width = tmpheight
		left = self.tempoffset['x'] / binscale
		top = self.tempoffset['y'] / binscale
		right = left + width
		bottom = top + height
		return acq_binning, left, top, right, bottom, width, height

	def _cropImage(self, image):
		# default no modification
		startx = self.getOffset()['x']
		starty = self.getOffset()['y']
		if startx != 0 or starty != 0:
			endx = self.dimension['x'] + startx
			endy = self.dimension['y'] + starty
			image = image[starty:endy,startx:endx]
			print 'cropped', image.shape
		return image

	def _modifyImageShape(self, image):
		print 'recieved', image.shape
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
		# K3 can not bin more than 2. Bin it here.
		added_binning = self.binning['x'] / self.acq_binning
		if added_binning > 1:
			image = imagefun_bin(image, added_binning)
		image = self._cropImage(image)
		self.debug_print('modified shape %s' % (image.shape,))
		return image
