#
# COPYRIGHT:
#      The Leginon software is Copyright 2003
#      The Scripps Research Institute, La Jolla, CA
#      For terms of the license agreement
#      see  http://ami.scripps.edu/software/leginon-license
#

#import array
import ccdcamera
import numpy
import sys
import threading
import enumproc
import killproc

import mmapfile
import pythoncom
import pywintypes
import win32com.client
import win32com.server.register

def listCamcProcs():
	procs = enumproc.EnumProcesses()
	camcprocs = []
	for proc in procs:
		if proc[:4].lower() == 'camc':
			camcprocs.append(proc)
	return camcprocs

def killCamc():
	killproc.Kill_Process('camc4')

def killCamcProcs():
	camcprocs = listCamcProcs()
	for camcproc in camcprocs:
		# remove .exe extension because Kill_Process does not use it
		procname = camcproc[:-4]
		killproc.Kill_Process(procname)

class CameraControl(object):
	def __init__(self):
		self.pingname = 'pyscope'
		self.cameralock = threading.RLock()
		self.camera = None
		self.cameras = []

	def addCamera(self, camera):
		self.lock()
		if camera in self.cameras:
			self.unlock()
			raise ValueError

		if not self.cameras:
			try:
				self.initialize()
			except:
				self.unlock()
				raise

		camera.setCameraType()

		try:
			hr = cameracontrol.camera.Initialize(camera.cameratype, 0)
		except pywintypes.com_error, e:
			self.unlock()
			raise RuntimeError('error initializing camera')
		except:
			self.unlock()
			raise

		self.cameras.append(camera)
		self.unlock()

	def removeCamera(self, camera):
		self.lock()
		self.cameras.remove(camera)

		if not self.cameras:
			try:
				self.uninitialize()
			except:
				self.unlock()
				raise

		self.unlock()

	def setCamera(self, camera):
		self.camera.ActiveCamera = camera.cameratype

	def lock(self):
		self.cameralock.acquire()

	def unlock(self):
		self.cameralock.release()

	def initialize(self):
		pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)

		try:
			self.camera = win32com.client.Dispatch('CAMC4.Camera')		
		except pywintypes.com_error, e:
			raise RuntimeError('failed to initialize interface CAMC4.Camera')

		try:
			ping = win32com.client.Dispatch('pyscope.CAMCCallBack')
		except pywintypes.com_error, e:
			raise RuntimeError('failed to initialize interface pyscope.Ping')

		try:
			hr = self.camera.RegisterCAMCCallBack(ping, self.pingname)
		except pywintypes.com_error, e:
			raise RuntimeError('error registering callback COM object')

		hr = self.camera.RequestLock()
		if hr == win32com.client.constants.crDeny:
			raise RuntimeError('error locking camera, denied lock')
		elif hr == win32com.client.constants.crBusy:
			raise RuntimeError('error locking camera, camera busy')
		elif hr == win32com.client.constants.crSucceed:
			pass

	def uninitialize(self):
		self.camera.UnlockCAMC()

cameracontrol = CameraControl()

class Tietz(object):
	cameratype = None
	mmname = ''
	dependencymapping = {
		'getChipName': [('cpChipName', 'r')],
		'getCameraName': [('cpCameraName', 'r')],
		'getCameraSize': [('cpTotalDimensionX', 'r'), ('cpTotalDimensionY', 'r')],
		'getPixelSize': [('cpPixelSizeX', 'r'), ('cpPixelSizeY', 'r')],
		'getMaximumPixelValue': [('cpDynamic', 'r')],
		'getNumberOfGains': [('cpNumberOfGains', 'r')],
		'getGainFactors': [('cpGainFactors', 'r')],
		'getNumberOfSpeeds': [('cpNumberOfSpeeds', 'r')],
		'getSpeeds': [('cpSpeeds', 'r')],
		'getLiveModeAvailable': [('cpLiveModeAvailable', 'r')],
		'getNumberOfDeadColumns': [('cpNumberOfDeadColumns', 'r')],
		'getDeadColumns': [('cpDeadColumns', 'r')],
		'getSimulationImagePath': [('cpImagePath', 'r')],
		'getGain': [('cpCurrentGainIndex', 'r'), ('cpGainFactors', 'r')],
		'getGainIndex': [('cpCurrentGainIndex', 'r')],
		'setGainIndex': [('cpCurrentGainIndex', 'w')],
		'getSpeed': [('cpCurrentSpeedIndex', 'r'), ('cpSpeeds', 'r')],
		'getSpeedIndex': [('cpCurrentSpeedIndex', 'r')],
		'setSpeedIndex': [('cpCurrentSpeedIndex', 'w')],
		'getImageTransform': [('cpImageGeometry', 'r')],
		'setImageTransform': [('cpImageGeometry', 'w')],
		'getTemperature': [('cpCurrentTemperature', 'r')],
		'setTemperature': [('cpTemperatureSetpoint', 'w')],
		'getShutterOpenDelay': [('cpShutterOpenDelay', 'r')],
		'setShutterOpenDelay': [('cpShutterOpenDelay', 'w')],
		'getShutterCloseDelay': [('cpShutterCloseDelay', 'r')],
		'setShutterCloseDelay': [('cpShutterCloseDelay', 'w')],
		'getSerialNumber': [('cpSerialNumber', 'r')],
		'getPreampDelay': [('cpPreampDelay', 'r')],
		'setPreampDelay': [('cpPreampDelay', 'w')],
		'getParallelMode': [('cpPMode', 'r')],
		'setParallelMode': [('cpPMode', 'w')],
		'getHardwareGainIndex': [('cpHWGainIndex', 'r')],
		'getHardwareSpeedIndex': [('cpHWSpeedIndex', 'r')],
		'getRetractable': [('cpIsRetractable', 'r')],
		'getCameraAxis': [('cpCameraPositionOnTem', 'r')],
		'setUseSpeedTableForGainSwitch': [('cpUseSpeedtabForGainSwitch', 'w')],
	}

	def __init__(self):
		killCamcProcs()
		self.unsupported = []

		#self.arraytypecode = 'H'
		self.imagetype = numpy.uint16
		self.bytesperpixel = 2

		self.binning = {'x': 1, 'y': 1}
		self.offset = {'x': 0, 'y': 0}
		self.dimension = {'x': 512, 'y': 512}
		self.exposuretime = 500
		self.exposuretype = 'normal'

		cameracontrol.addCamera(self)

		for methodname, dependencies in self.dependencymapping.items():
			supported = True
			for dependency in dependencies:
				parametername, permission = dependency
				if permission not in self._getParameterPermissions(parametername):
					supported = False
			if not supported:
				self.unsupported.append(methodname)

		## some cameras require centered geometries
		geo = self.calculateCenteredGeometry(self.dimension['x'], self.binning['x'])
		self.setGeometry(geo)

	def setCameraType(self):
		self.cameratype = getattr(win32com.client.constants, self.cameratypeattr)

	def __getattribute__(self, attr_name):
		if attr_name in object.__getattribute__(self, 'unsupported'):
			raise AttributeError('attribute not supported')
		return object.__getattribute__(self, attr_name)

	def _getParameterPermissions(self, parametername):
		try:
			parameter = getattr(win32com.client.constants, parametername)
		except:
			return ''
		cameracontrol.lock()
		cameracontrol.setCamera(self)
		value = cameracontrol.camera.QueryParameter(parameter)
		cameracontrol.unlock()
		if value in (5, 9):
			return 'r'
		elif value in (6, 10):
			return 'w'
		elif value in (7, 11):
			return 'rw'
		return ''

	def _getParameterType(self, parametername):
		try:
			parameter = getattr(win32com.client.constants, parametername)
		except:
			return None
		cameracontrol.lock()
		cameracontrol.setCamera(self)
		value = cameracontrol.camera.QueryParameter(parameter)
		cameracontrol.unlock()
		if value in (5, 6, 7):
			return int
		elif value in (9, 10, 11):
			return str
		return None

	def _getParameterValue(self, parametername):
		parametertype = self._getParameterType(parametername)
		if parametertype is None:
			return None
		try:
			parameter = getattr(win32com.client.constants, parametername)
		except:
			return None
		cameracontrol.lock()
		cameracontrol.setCamera(self)
		if parametertype is int:
			result = cameracontrol.camera.LParam(parameter)
		elif parametertype is str:
			result = cameracontrol.camera.SParam(parameter)
		else:
			result = None
		cameracontrol.unlock()
		return result

	def _setParameterValue(self, parametername, value):
		parametertype = self._getParameterType(parametername)
		if parametertype is None:
			return None
		try:
			parameter = getattr(win32com.client.constants, parametername)
		except:
			return None
		cameracontrol.lock()
		cameracontrol.setCamera(self)
		if parametertype is int:
			result = cameracontrol.camera.SetLParam(parameter, value)
		elif parametertype is str:
			result = cameracontrol.camera.SetSParam(parameter, value)
		else:
			result = None
		cameracontrol.unlock()
		return result

	def exit(self):
		cameracontrol.camera.UnInitialize(self.cameratype)
		cameracontrol.removeCamera(self)

	def __del__(self):
		try:
			self.exit()
		except:
			pass
	
	def getOffset(self):
		return dict(self.offset)

	def setOffset(self, value):
		# {'type': dict,
		#		'values': {'x':
		#						{'type': int,
		#							'range': [0, camerasize['x'] - dimension['x']*binning['x']]},
		#								'y':
		#						{'type': int,
		#							'range': [0, camerasize['y'] - dimension['y']*binning['y']]}}}
		self.offset = dict(value)

	def getDimension(self):
		return dict(self.dimension)

	def setDimension(self, value):
		# {'type': dict,
		#		'values': {'x':
		#						{'type': int,
		#							'range': [0, (camerasize['x'] - offset['x'])/binning['x']]},
		#								'y':
		#						{'type': int,
		#							'range': [0, (camerasize['y'] - offset['y'])/binning['y']]}}}
		self.dimension = dict(value)

	def getBinning(self):
		return dict(self.binning)

	def setBinning(self, value):
		# {'type': dict,
		#		'values': {'x':
		#					{'type': int,
		#						'range': [1, (camerasize['x'] - offset['x'])/dimension['x']]},
		#								'y':
		#					{'type': int,
		#						'range': [1, (camerasize['y'] - offset['y'])/dimension['y']]}}}
		self.binning = dict(value)

	def getExposureTime(self):
		return float(self.exposuretime)

	def setExposureTime(self, value):
		# {'type': int, 'range': [0, None]
		self.exposuretime = int(round(value))

	def getExposureTypes(self):
		return ['normal', 'dark', 'bias', 'readout']

	def getExposureType(self):
		return self.exposuretype

	def setExposureType(self, value):
		# {'type': str, 'values': ['normal', 'dark', 'bias', 'readout']}
		if value not in ['normal', 'dark', 'bias', 'readout']:
			raise ValueError('invalid exposure type')
		self.exposuretype = value

	def _getImage(self):
		# {'type': numpy.ndarray}
		# 0 uses internal flash signal
		# 1 uses internal exposure signal (PVCam and PXL only)
		# shutter_mode = 1

		offset = dict(self.getOffset())
		dimension = self.getDimension()
		binning = self.getBinning()

		camerasize = self.getCameraSize()

		mirror = self.getMirror()
		if mirror == 'vertical':
			offset['x'] = camerasize['x']/binning['x'] - offset['x'] - dimension['x']
		elif mirror == 'horizontal':
			offset['y'] = camerasize['y']/binning['y'] - offset['y'] - dimension['y']
		elif mirror == 'both':
			offset['x'] = camerasize['x']/binning['x'] - offset['x'] - dimension['x']
			offset['x'] = camerasize['x']/binning['x'] - offset['x'] - dimension['x']

		# rotation untested
		rotation = self.getRotation()
		if rotation == 90:
			offset['x'] = camerasize['y']/binning['y'] - offset['y'] - dimension['y']
			offset['y'] = offset['x']
		elif rotation == 180:
			offset['x'] = camerasize['x']/binning['x'] - offset['x'] - dimension['x']
			offset['y'] = camerasize['y']/binning['y'] - offset['y'] - dimension['y']
		elif rotation == 270:
			offset['x'] = offset['y']
			offset['y'] = camerasize['x']/binning['x'] - offset['x'] - dimension['x']

		cameracontrol.lock()
		cameracontrol.setCamera(self)
		hr = cameracontrol.camera.Format(
														offset['x']*binning['x'], offset['y']*binning['y'],
														dimension['x'], dimension['y'],
														binning['x'], binning['y'])
		exposuretype = self.getExposureType()
		if exposuretype == 'normal':
			hr = cameracontrol.camera.AcquireImage(self.getExposureTime(), 0)
		elif exposuretype == 'dark':
			hr = cameracontrol.camera.AcquireDark(self.getExposureTime(), 0)
		elif exposuretype == 'bias':
			hr = cameracontrol.camera.AcquireBias(0)
		elif exposuretype == 'readout':
			hr = cameracontrol.camera.AcquireReadout(0)
		else:
			cameracontrol.unlock()
			raise ValueError('invalid exposure type for image acquisition')
		cameracontrol.unlock()

		imagesize = self.bytesperpixel*dimension['x']*dimension['y']

		map = mmapfile.mmapfile('', self.mmname, imagesize)
		#na = numpy.array(array.array(self.arraytypecode, map.read(imagesize)),
		#										self.imagetype)
		na = numpy.fromstring(map.read(imagesize), self.imagetype)
		map.close()
		na.shape = (dimension['y'], dimension['x'])
		return na

	def getChipName(self):
		# {'type': str}
		return self._getParameterValue('cpChipName')

	def getCameraName(self):
		# {'type': str}
		return self._getParameterValue('cpCameraName')

	def getCameraSize(self):
		# {'type': dict, 'values': {'x': {'type': int}, 'y': {'type': int}}}}
		x = self._getParameterValue('cpTotalDimensionX')
		y = self._getParameterValue('cpTotalDimensionY')
		return {'x': x, 'y': y}

	def getPixelSize(self):
		# {'type': dict, 'values': {'x': {'type': float}, 'y': {'type': float}}}}
		x = self._getParameterValue('cpPixelSizeX')/1e9
		y = self._getParameterValue('cpPixelSizeY')/1e9
		return {'x': x, 'y': y}

	def getMaximumPixelValue(self):
		# {'type': int}
		return self._getParameterValue('cpDynamic')

	def getNumberOfGains(self):
		# {'type': int}
		return self._getParameterValue('cpNumberOfGains')

	# eval...
	def getGainFactors(self):
		# {'type': list}
		return list(eval(self._getParameterValue('cpGainFactors')))

	def getNumberOfSpeeds(self):
		# {'type': int}
		return self._getParameterValue('cpNumberOfSpeeds')

	# eval...
	def getSpeeds(self):
		# {'type': list}
		return list(eval(self._getParameterValue('cpSpeeds')))

	def getLiveModeAvailable(self):
		# {'type': bool}
		value = self._getParameterValue('cpLiveModeAvailable')
		if value == 1:
			return True
		elif value == 0:
			return False
		raise RuntimeError('unknown live mode available value')

	def getNumberOfDeadColumns(self):
		# {'type': int}
		return self._getParameterValue('cpNumberOfDeadColumns')

	# eval...
	def getDeadColumns(self):
		# {'type': list}
		return eval(self._getParameterValue('cpDeadColumns'))

	def getSimulationImagePath(self):
		# {'type': str}
		return self._getParameterValue('cpImagePath')

	def getGainIndex(self):
		return self._getParameterValue('cpCurrentGainIndex')

	def getGain(self):
		# {'type': int}
		return self.getGainFactors()[self.getGainIndex() - 1]

	def setGainIndex(self, value):
		# {'type': int, 'range': [1, self.getNumberOfGains()]}
		try:
			self._setParameterValue('cpCurrentGainIndex', value)
		except pywintypes.com_error:
			raise ValueError('invalid gain index specified')

	def getSpeedIndex(self):
		return self._getParameterValue('cpCurrentSpeedIndex')

	def getSpeed(self):
		# {'type': int}
		return self.getSpeeds()[self.getSpeedIndex() - 1]

	def setSpeedIndex(self, value):
		# {'type': int, 'range': [1, self.getNumberOfSpeeds()]}
		try:
			self._setParameterValue('cpCurrentSpeedIndex', value)
		except pywintypes.com_error:
			raise ValueError('invalid speed index specified')

	def getMirrorStates(self):
		return ['none', 'horizontal', 'vertical', 'both']

	def getMirror(self):
		bitmask = self._getParameterValue('cpImageGeometry')
		mirror = []
		if bitmask & 1 and bitmask & 2:
			return 'both'
		elif bitmask & 1: # mirrored horizontal
			return 'horizontal'
		elif bitmask & 2: # mirrored vertical
			return 'vertical'
		return 'none'

	def getRotations(self):
		return [0, 90, 180, 270]

	def getRotation(self):
		bitmask = self._getParameterValue('cpImageGeometry')

		rotation = 0
		if bitmask & 4: # rotated 90 degrees CCW
			rotation += 90
		if bitmask & 8: # rotated 180 degrees
			rotation += 180
		if bitmask & 16: # rotated 90 degrees CW
			rotation += 270
		rotation %= 360

		return rotation

	def setMirror(self, value):
		bitmask = self._getParameterValue('cpImageGeometry')
		bitmask &= 28
		if value == 'horizontal':
			bitmask |= 1
		elif value == 'vertical':
			bitmask |= 2
		elif value == 'both':
			bitmask |= 3
		elif value == 'none':
			pass
		else:
			raise ValueError
		self._setParameterValue('cpImageGeometry', bitmask)

	def setRotation(self, value):
		bitmask = self._getParameterValue('cpImageGeometry')
		bitmask &= 3

		if value['rotation'] == 0:
			pass
		elif value['rotation'] == 90:
			bitmask |= 4
		elif value['rotation'] == 180:
			bitmask |= 8
		elif value['rotation'] == 270:
			bitmask |= 16
		else:
			raise ValueError

		self._setParameterValue('cpImageGeometry', bitmask)

	def getTemperature(self):
		return self._getParameterValue('cpCurrentTemperature')/1000.0

	def setTemperature(self, value):
		#	{'type': float}
		self._setParameterValue('cpTemperatureSetpoint', int(value*1000))

	def getShutterOpenDelay(self):
		return self._getParameterValue('cpShutterOpenDelay')

	def setShutterOpenDelay(self, value):
		#	{'type': int, 'range': [0, None]}
		try:
			self._setParameterValue('cpShutterOpenDelay', value)
		except pywintypes.com_error:
			raise ValueError('invalid shutter open delay')

	def getShutterCloseDelay(self):
		return self._getParameterValue('cpShutterCloseDelay')

	def setShutterCloseDelay(self, value):
		#	{'type': int, 'range': [0, None]}
		try:
			self._setParameterValue('cpShutterCloseDelay', value)
		except pywintypes.com_error:
			raise ValueError('invalid shutter close delay')

	def setShutter(self, state):
		if state == 'open':
			if self.theAda.OpenShutter != 0:
				raise RuntimeError('open shutter failed')
		elif state == 'closed':
			if self.theAda.CloseShutter != 0:
				raise RuntimeError('close shutter failed')
		else:
			raise ValueError('setShutter state must be \'open\' or \'closed\', not %s' % (state,))

	def getShutter(self):
		status = self.theAda.ShutterStatus
		if status:
			return 'closed'
		else:
			return 'open'

	def getSerialNumber(self):
		# {'type': str}
		return self._getParameterValue('cpSerialNumber')
			
	def getPreampDelay(self):
		return self._getParameterValue('cpPreampDelay')

	def setPreampDelay(self, value):
		#	{'type': int, 'range': [0, None]}
		try:
			self._setParameterValue('cpPreampDelay', value)
		except pywintypes.com_error:
			raise ValueError('invalid preamp delay')

	# PMode boolean?
	def getParallelMode(self):
		if self._getParameterValue('cpPMode'):
			return True
		return False

	# PMode boolean?
	def setParallelMode(self, value):
		#	{'type': bool}
		try:
			if value:
				self._setParameterValue('cpPMode', 1)
			else:
				self._setParameterValue('cpPMode', 0)
		except pywintypes.com_error:
			raise ValueError('invalid parallel mode')

	def setUseSpeedTableForGainSwitch(self, value):
		#	{'type': bool}
		if value:
			value = 1
		else:
			value = 0
		self._setParameterValue('cpUseSpeedtabForGainSwitch', value)

	def getHardwareGainIndex(self):
		# {'type': int}
		return self._getParameterValue('cpHWGainIndex')

	def getHardwareSpeedIndex(self):
		# {'type': int}
		return self._getParameterValue('cpHWSpeedIndex')

	def getRetractable(self):
		# {'type': bool}
		value = self._getParameterValue('cpIsRetractable')
		if value:
			return True
		else:
			return False

	def getCameraAxis(self):
		# {'type': str}
		value = self._getParameterValue('cpCameraPositionOnTem')
		if value == 0:
			return 'on'
		elif value == 1:
			return 'off'
		else:
			raise RuntimeError('error getting camera axis')

class TietzPXL(Tietz, ccdcamera.CCDCamera):
	name = 'Tietz PXL'
	try:
		cameratype = win32com.client.constants.ctPXL
	except:
		pass
	mmname = 'CAM_PXL_DATA'
	def __init__(self):
		ccdcamera.CCDCamera.__init__(self)
		Tietz.__init__(self)
	
class TietzSimulation(Tietz, ccdcamera.CCDCamera):
	name = 'Tietz Simulation'
	try:
		cameratype = win32com.client.constants.ctSimulation
	except:
		pass
	mmname = 'CAM_SIMU_DATA'
	def __init__(self):
		ccdcamera.CCDCamera.__init__(self)
		Tietz.__init__(self)

class TietzPVCam(Tietz, ccdcamera.CCDCamera):
	name = 'Tietz PVCam'
	try:
		cameratype = win32com.client.constants.ctPVCam
	except:
		pass
	mmname = 'CAM_PVCAM_DATA'
	def __init__(self):
		ccdcamera.CCDCamera.__init__(self)
		Tietz.__init__(self)
	
class TietzFastScan(Tietz, ccdcamera.FastCCDCamera):
	name = 'Tietz FastScan'
	try:
		cameratype = win32com.client.constants.ctFastScan
	except:
		pass
	mmname = 'CAM_FASTSCAN_DATA'
	def __init__(self):
		ccdcamera.CCDCamera.__init__(self)
		Tietz.__init__(self)
	
class TietzFastScanFW(Tietz, ccdcamera.FastCCDCamera):
	name = 'Tietz FastScan Firewire'
	try:
		cameratype = win32com.client.constants.ctF114_FW
	except:
		pass
	mmname = 'CAM_FSFW_DATA'
	def __init__(self):
		ccdcamera.CCDCamera.__init__(self)
		Tietz.__init__(self)
	
class TietzSCX(Tietz, ccdcamera.CCDCamera):
	name = 'Tietz SCX'
	cameratypeattr = 'ctSCX'
	mmname = 'CAM_SCX_DATA'
	def __init__(self):
		ccdcamera.CCDCamera.__init__(self)
		Tietz.__init__(self)

class TietzFC415(Tietz, ccdcamera.CCDCamera):
	name = 'Tietz FC415'
	try:
		cameratype = win32com.client.constants.ctFC415
	except:
		pass
	mmname = 'CAM_FC415_DATA'
	def __init__(self):
		ccdcamera.CCDCamera.__init__(self)
		Tietz.__init__(self)
