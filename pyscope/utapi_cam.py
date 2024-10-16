#!/usr/bin/env python3
SIMULATION = False
import numpy
import time

if not SIMULATION:
	from pyscope import ccdcamera
	import grpc
	from google.protobuf import json_format as json_format

	# requests builders
	from utapi_types.v1 import device_id_pb2 as dip
	from utapi_types.v1 import utapi_response_pb2 as urp
	from acquisition.v1 import acquisition_pb2 as acq_p
	from acquisition.v1 import camera_single_pb2 as cam_p
	from acquisition.v1 import stem_raster_acquisition_pb2 as stcam_p
	from acquisition.v1 import camera_types_pb2 as camtypes_p

	# used to create stub for access
	from acquisition.v1 import acquisition_pb2_grpc as acq_pg
	from acquisition.v1 import camera_single_pb2_grpc as cam_pg
	from acquisition.v1 import stem_raster_acquisition_pb2_grpc as stcam_pg

	channel = grpc.insecure_channel('localhost:46699', options=[('grpc.max_receive_message_length', 200 * 1024 * 1024)])

	acq_stub = acq_pg.AcquisitionServiceStub(channel)
	cam_stub = cam_pg.CameraSingleServiceStub(channel)
	stcam_stub = stcam_pg.StemRasterAcquisitionServiceStub(channel)

	
def handleRpcError(e):
	if e.code() == grpc.StatusCode.ABORTED:
		utapi_response = urp.UtapiResponse()
		utapi_response.ParseFromString(e.trailing_metadata()[0][1])
		print(f"Error with UtapiResponse>\n{utapi_response}<")
	else:
		# Not an UtapiResponse. rethrow exception
		raise

def _response_to_dict(response):
	if SIMULATION:
		return response
	return json_format.MessageToDict(response)

def _get_by_request(stub,attr_name,request):
	print('_get_by_request',stub, attr_name, request)
	my_attr = getattr(stub,attr_name)
	try:
		# perform my_attr action on the request and convert to list and dict
		return _response_to_dict(my_attr(request))
	except grpc.RpcError as rpc_error:
		handleRpcError(rpc_error)

def _set_by_request(stub, attr_name, request):
	print('_set_by_request',stub, attr_name, request)
	my_attr = getattr(stub,attr_name)
	try:
		# perform my_attr action on the request
		return my_attr(request)
	except grpc.RpcError as rpc_error:
		handleRpcError(rpc_error)

def getAllStemCamera():
	my_request = acq_p.DeviceQueryRequest(mode=1,type=3)

class Ceta(ccdcamera.CCDCamera):
	name = 'Ceta'
	camera_name = 'BM-Ceta'
	binning_limits = [1,2,4,8]
	intensity_averaged = False
	utapi_device_id_name = 'Ceta 16M BottomMounted'

	def getDebugCamera(self):
		return True

	def __init__(self):
		self.unsupported = []
		ccdcamera.CCDCamera.__init__(self)
		self.device = dip.DeviceId(id=self.utapi_device_id_name)
		self.save_frames = False
		self.batch = False
		self.frames_name_set_by_leginon=False
		self.setReadoutLimits()
		self.initSettings()
		#self.setFrameFormatFromConfig()
		self.setUseCameraQueue()

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
		self.camera_settings_request = None

	def setReadoutLimits(self):
		readout_dicts = {'FIXED_READOUT_AREA_FULL':1,'FIXED_READOUT_AREA_HALF':2,'FIXED_READOUT_AREA_QUARTER':4}
		self.sorted_readout_keys = ('FIXED_READOUT_AREA_QUARTER', 'FIXED_READOUT_AREA_HALF', 'FIXED_READOUT_AREA_FULL')
		self.readout_id_map = {}
		for k in self.sorted_readout_keys:
			const = getattr(camtypes_p,k)
			self.readout_id_map[const] = k
		size = self.getCameraSize()
		# before binning
		self.limit_dim = {}
		self.limit_off = {}
		for k in self.sorted_readout_keys:
			self.limit_dim[k] = {'x': int(size['x']/readout_dicts[k]), 'y': int(size['y']/readout_dicts[k])}
			self.limit_off[k] = {'x': int((size['x']-self.limit_dim[k]['x'])/2.0), 'y':int((size['y']-self.limit_dim[k]['y'])/2.0)}
		self.readout_offset = {'x':0,'y':0}

	def setUseCameraQueue(self):
		self.use_queue = False

	def getCameraBinnings(self):
		return self.binning_limits

	def setBinning(self, value):
		self.binning = value

	def getBinning(self):
		return self.binning

	def getIntensityAveraged(self):
		return self.intensity_averaged

	def setDimension(self, value):
		self.dimension = value

	def getDimension(self):
		return self.dimension

	def setOffset(self, value):
		self.offset = value

	def getOffset(self):
		return self.offset

	def setExposureTime(self, ms):
		# milliseconds
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

	def _getReadoutAreaKey(self,unbindim, unbinoff):
		size = self.getCameraSize()
		if unbindim['x']+unbinoff['x'] > size['x'] or unbindim['y']+unbinoff['y'] > size['y']:
			raise ValueError('defined readout area outside the camera')
		for k in self.sorted_readout_keys:
			limit_off = self.limit_off[k]
			limit_dim = self.limit_dim[k]
			if (unbinoff['x'] >= limit_off['x']
				and unbinoff['y'] >= limit_off['y']
				and	unbinoff['x']+unbindim['x'] <= limit_dim['x']+limit_off['x']
				and unbinoff['y']+unbindim['y'] <= limit_dim['y']+limit_off['y']):
				return k
		raise ValueError('Does not fit any defined readout area')

	def _getReadoutOffset(self, key, binned_full_off):
		limit_off = self.limit_off[key]
		return {'x':binned_full_off['x']-limit_off['x']//self.binning['x'],'y':binned_full_off['x']-limit_off['y']//self.binning['y']}

	def finalizeSetup(self):
		self.camera_settings_request = cam_p.StartSingleAcquisitionRequest(device_id=self.device)
		# final bin
		binning = self.binning
		# final range
		unbindim = {'x':self.dimension['x']*binning['x'], 'y':self.dimension['y']*binning['y']}
		unbinoff = {'x':self.offset['x']*binning['x'], 'y':self.offset['y']*binning['y']}
		readout_key = self._getReadoutAreaKey(unbindim, unbinoff)
		exposure_s = self.exposure/1000.0 #seconds

		setattr(self.camera_settings_request, 'pixel_binning_width', binning['x'])
		setattr(self.camera_settings_request,'pixel_binning_height', binning['y'])
		setattr(self.camera_settings_request,'fixed_readout_area', getattr(camtypes_p,readout_key))
		setattr(self.camera_settings_request,'exposure_time',exposure_s)

	def _getConfig(self, param):
		if param == 'readout':
			return self.readout_id_map[self.camera_settings_request.fixed_readout_area]
		elif param == 'binning':
			return {'x':self.camera_settings_request.pixel_binning_width,'y':self.camera_settings_request.pixel_binning_height}
		elif param == 'exposure':
			return self.camera_settings_request.exposure_time

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
		#while self.csa.IsActive:
		#	time.sleep(0.1)
		if self.readoutcallback:
			name = str(time.time())
			self.registerCallback(name, self.readoutcallback)
			self.backgroundReadout(name)
		else:
			if self.getExposureType() == 'dark':
				result=self._getFakeDark()
			elif self.getExposureType() != 'norm':
				result=self._getImage()
			else:
				result= self._getSavedNorm()
			return result

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
		arr = numpy.zeros((limit_dim['y']//self.binning['y'],limit_dim['x']//self.binning['x']))
		self.image_metadata = {}
		if self.getDebugCamera():
			print('got arr and to modify')
		arr = self.modifyImage(arr)
		return arr

	def _getImageArray(self, acq_id):
		if self.batch and self.save8x8 and ((hasattr(self, 'save_frames') and self.save_frames) or (hasattr(self, 'align_frames') and self.algn_frames)):
			if self.getDebugCamera():
				print('fake 8x8')
			# This is 0.20 s faster than get array and then make fake for 1 s exposure.
			fake_std = 50
			fake_mean = 4000
			arr = self.base_fake_image*fake_std + fake_mean*numpy.ones((8,8))
			return arr
		# get from camera
		wait_request = cam_p.WaitForSingleAcquisitionRequest(acquisition_id=acq_id, progress_point=5)
		response = _set_by_request(cam_stub,'WaitForSingleAcquisition',wait_request)
		fdata = response.final_image
		image_shape = (fdata.y_size,fdata.x_size)
		array = numpy.frombuffer(fdata.data,dtype=numpy.int32)
		array = array.reshape(image_shape)
		return array

	def _getImageAcqId(self):
		param_req = self.camera_settings_request
		acq_id = _get_by_request(cam_stub,'StartSingleAcquisition', param_req)['acquisitionId']
		return acq_id

	def custom_setup(self):
		pass

	def _modifyArray(self, arr):
		rk = self._getConfig('readout')
		arr = arr.reshape((self.limit_dim[rk]['y']//self.binning['y'],self.limit_dim[rk]['x']//self.binning['x']))
		return arr

	def modifyImage(self, arr):
		rk = self._getConfig('readout')
		print('readout',rk)
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
		uncropped_readout = {'x':arr.shape[1],'y':arr.shape[0]}
		try:
			if self.dimension['x'] < arr.shape[1]:
				arr=arr[:,readout_offset['x']:readout_offset['x']+self.dimension['x']]
			if self.dimension['y'] < arr.shape[0]:
				arr=arr[readout_offset['y']:readout_offset['y']+self.dimension['y'],:]
			if self.getDebugCamera():
				print('cropped %s to offset %s and dim %s' %(uncropped_readout, readout_offset,self.dimension))
		except Exception as e:
			if self.getDebugCamera():
				print('croping %s to offset %s and dim %s failed' %(uncropped_readout, readout_offset,self.dimension))
			raise
		# TO DO: Maybe need to scale ?
		if SIMULATION and self.getIntensityAveraged():
			arr = arr / (self.getExposureTime()/1000.0)
		return arr

	def _getImage(self):
		'''
		Acquire an image using the setup for this client. The image should be a two-dimensional array.
		'''
		try:
			self.finalizeSetup()
			self.custom_setup()
		except Exception as e:
			if self.getDebugCamera():
				print('Camera setup',e)
			raise RuntimeError('Error setting camera parameters: %s' % (e,))
		try:
			acq_id=self._getImageAcqId()
			arr = self._getImageArray(acq_id)
		except Exception as e:
			print('Camera acquire array',e)
			raise RuntimeError('Error getting camera array: %s' % (e,))
		arr = self.modifyImage(arr)
		return arr	
