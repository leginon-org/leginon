#
# COPYRIGHT:
#      The Leginon software is Copyright 2003
#      The Scripps Research Institute, La Jolla, CA
#      For terms of the license agreement
#      see  http://ami.scripps.edu/software/leginon-license
#

#import array
import ccdcamera
import numarray
import sys

try:
	import mmapfile
	import pythoncom
	import pywintypes
	import win32com.client
	import win32com.server.register
	try:
		import tietzcom
	except ImportError:
		import pyScope.tietzcom as tietzcom
except ImportError:
	pass

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
		self.unsupported = []

		if self.cameratype is None:
			raise NotImplementedError('Tietz virtual class')

		#self.arraytypecode = 'H'
		self.imagetype = numarray.UInt16
		self.bytesperpixel = 2

		self.binning = {'x': 1, 'y': 1}
		self.offset = {'x': 0, 'y': 0}
		self.dimension = {'x': 512, 'y': 512}
		self.exposuretime = 500
		self.exposuretype = 'normal'

		pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)

		try:
			self.camera = win32com.client.Dispatch('CAMC4.Camera')		
		except pywintypes.com_error, e:
			raise RuntimeError('failed to initialize interface CAMC4.Camera')

		try:
			ping = win32com.client.Dispatch('pyScope.CAMCCallBack')
		except pywintypes.com_error, e:
			raise RuntimeError('failed to initialize interface pyScope.Ping')

		try:
			hr = self.camera.RegisterCAMCCallBack(ping, 'EM')
		except pywintypes.com_error, e:
			raise RuntimeError('error registering callback COM object')

		hr = self.camera.RequestLock()
		if hr == win32com.client.constants.crDeny:
			raise RuntimeError('error locking camera, denied lock')
		elif hr == win32com.client.constants.crBusy:
			raise RuntimeError('error locking camera, camera busy')
		elif hr == win32com.client.constants.crSucceed:
			pass

		try:
			hr = self.camera.Initialize(self.cameratype, 0)
		except pywintypes.com_error, e:
			raise RuntimeError('error initializing camera')

		self.methodmapping = {
			'binning': {'get':'getBinning',
									'set': 'setBinning'},
			'dimension': {'get':'getDimension',
										'set': 'setDimension'},
			'offset': {'get':'getOffset',
									'set': 'setOffset'},
			'exposure time': {'get':'getExposureTime',
												'set': 'setExposureTime'},
			'exposure type': {'get':'getExposureType',
												'set': 'setExposureType'},
			'image data': {'get':'getImage'},
			'chip name': {'get':'getChipName'},
			'camera name': {'get':'getCameraName'},
			'camera size': {'get':'getCameraSize'},
			'pixel size': {'get':'getPixelSize'},
			'maximum pixel value': {'get':'getMaximumPixelValue'},
			'number of gains': {'get':'getNumberOfGains'},
			'gain factors': {'get':'getGainFactors'},
			'number of speeds': {'get':'getNumberOfSpeeds'},
			'speeds': {'get':'getSpeeds'},
			'live mode available': {'get':'getLiveModeAvailable'},
			'number of dead columns': {'get':'getNumberOfDeadColumns'},
			'dead columns': {'get':'getDeadColumns'},
			'simulation image path': {'get':'getSimulationImagePath'},
			'gain': {'get':'getGain'},
			'gain index': {'get':'getGainIndex',
											'set': 'setGainIndex'},
			'speed': {'get':'getSpeed'},
			'speed index': {'get':'getSpeedIndex',
															'set': 'setSpeedIndex'},
			'image transform': {'get':'getImageTransform',
													'set': 'setImageTransform'},
			'temperature': {'get':'getTemperature',
											'set': 'setTemperature'},
			'shutter open delay': {'get':'getShutterOpenDelay',
															'set': 'setShutterOpenDelay'},
			'shutter close delay': {'get':'getShutterCloseDelay',
															'set': 'setShutterCloseDelay'},
			'serial number': {'get':'getSerialNumber'},
			'preamp delay': {'get':'getPreampDelay',
												'set': 'setPreampDelay'},
			'parallel mode': {'get':'getParallelMode',
												'set': 'setParallelMode'},
			'hardware gain index': {'get':'getHardwareGainIndex'},
			'hardware speed index': {'get':'getHardwareSpeedIndex'},
			'retractable': {'get':'getRetractable'},
			'camera axis': {'get':'getCameraAxis'},
			'speed table gain switch': {'set': 'setUseSpeedTableForGainSwitch'},
			'dump': {'set': 'dumpImage', 'get': 'getDump'},
		}

		self.typemapping = {
			'binning': {'type': dict, 'values':
																		{'x': {'type': int}, 'y': {'type': int}}},
			'dimension': {'type': dict, 'values':
																		{'x': {'type': int}, 'y': {'type': int}}},
			'offset': {'type': dict, 'values':
																		{'x': {'type': int}, 'y': {'type': int}}},
			'exposure time': {'type': int},
			'exposure type': {'type': str,
												'values': ['normal', 'dark', 'bias', 'readout']},
			'image data': {'type': numarray.ArrayType},
			'chip name': {'type': str},
			'camera name': {'type': str},
			'camera size': {'type': dict, 'values':
																		{'x': {'type': int}, 'y': {'type': int}}},
			'pixel size': {'type': dict, 'values':
																	{'x': {'type': float}, 'y': {'type': float}}},
			'maximum pixel value': {'type': int},
			'number of gains': {'type': int},
			'gain factors': {'type': list},
			'number of speeds': {'type': int},
			'speeds': {'type': list},
			'live mode available': {'type': bool},
			'number of dead columns': {'type': int},
			'dead columns': {'type': list},
			'simulation image path': {'type': str},
			'gain': {'type': int},
			'gain index': {'type': int},
			'speed': {'type': int},
			'speed index': {'type': int},
			'image transform': {'type': dict, 'values':
							{'mirror': {'type': str, 'values': ['horizontal', 'vertical']},
								'rotation': {'type': int,	'values': [0, 90, 180, 270]}}},
			'temperature': {'type': float},
			'shutter open delay': {'type': int},
			'shutter close delay': {'type': int},
			'serial number': {'type': str},
			'preamp delay': {'type': int},
			'parallel mode': {'type': bool},
			'hardware gain index': {'type': int},
			'hardware speed index': {'type': int},
			'retractable': {'type': bool},
			'camera axis': {'type': str},
			'speed table gain switch': {'type': bool},
			'dump': {'type': bool},
		}

		for methodname, dependencies in self.dependencymapping.items():
			supported = True
			for dependency in dependencies:
				parametername, permission = dependency
				if permission not in self._getParameterPermissions(parametername):
					supported = False
			if not supported:
				#object.__getattribute__(self, 'unsupported').append(methodname)
				self.unsupported.append(methodname)
				for key, methods in self.methodmapping.items():
					for methodtype, method in methods.items():
						if method == methodname:
							del methods[methodtype]

	def __getattribute__(self, attr_name):
		if attr_name in object.__getattribute__(self, 'unsupported'):
			raise AttributeError('attribute not supported')
		return object.__getattribute__(self, attr_name)

	def _getParameterPermissions(self, parametername):
		try:
			parameter = getattr(win32com.client.constants, parametername)
		except:
			return ''
		value = self.camera.QueryParameter(parameter)
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
		value = self.camera.QueryParameter(parameter)
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
		if parametertype is int:
			return self.camera.LParam(parameter)
		elif parametertype is str:
			return self.camera.SParam(parameter)
		return None

	def _setParameterValue(self, parametername, value):
		parametertype = self._getParameterType(parametername)
		if parametertype is None:
			return None
		try:
			parameter = getattr(win32com.client.constants, parametername)
		except:
			return None
		if parametertype is int:
			return self.camera.SetLParam(parameter, value)
		elif parametertype is str:
			return self.camera.SetSParam(parameter, value)
		return None

	def exit(self):
		self.camera.UnlockCAMC()

	def __del__(self):
		try:
			self.camera.UnlockCAMC()
		except:
			pass
	
	def getOffset(self):
		return self.offset

	def setOffset(self, value):
		# {'type': dict,
		#		'values': {'x':
		#						{'type': int,
		#							'range': [0, camerasize['x'] - dimension['x']*binning['x']]},
		#								'y':
		#						{'type': int,
		#							'range': [0, camerasize['y'] - dimension['y']*binning['y']]}}}
		self.offset = value

	def getDimension(self):
		return self.dimension

	def setDimension(self, value):
		# {'type': dict,
		#		'values': {'x':
		#						{'type': int,
		#							'range': [0, (camerasize['x'] - offset['x'])/binning['x']]},
		#								'y':
		#						{'type': int,
		#							'range': [0, (camerasize['y'] - offset['y'])/binning['y']]}}}
		self.dimension = value

	def getBinning(self):
		return self.binning

	def setBinning(self, value):
		# {'type': dict,
		#		'values': {'x':
		#					{'type': int,
		#						'range': [1, (camerasize['x'] - offset['x'])/dimension['x']]},
		#								'y':
		#					{'type': int,
		#						'range': [1, (camerasize['y'] - offset['y'])/dimension['y']]}}}
		self.binning = value

	def getExposureTime(self):
		return self.exposuretime

	def setExposureTime(self, value):
		# {'type': int, 'range': [0, None]
		self.exposuretime = value

	def getExposureType(self):
		return self.exposuretype

	def setExposureType(self, value):
		# {'type': str, 'values': ['normal', 'dark', 'bias', 'readout']}
		if value not in ['normal', 'dark', 'bias', 'readout']:
			raise ValueError('invalid exposure type')
		self.exposuretype = value

	def dumpImage(self, value):
		if not value:
			return
		## could this be fast if we force a large binning on it?
		hr = self.camera.AcquireReadout(0)

	def getDump(self):
		return False
	
	def getImage(self):
		# {'type': numarray.ArrayType}
		# 0 uses internal flash signal
		# 1 uses internal exposure signal (PVCam and PXL only)
		# shutter_mode = 1

		offset = dict(self.getOffset())
		dimension = self.getDimension()
		binning = self.getBinning()

		imagetransform = self.getImageTransform()
		if imagetransform['mirror']:
			camerasize = self.getCameraSize()
		if 'vertical' in imagetransform['mirror']:
			offset['x'] = camerasize['x']/binning['x'] - offset['x'] - dimension['x']
		if 'horizontal' in imagetransform['mirror']:
			offset['y'] = camerasize['y']/binning['y'] - offset['y'] - dimension['y']

		# rotation untested
		if imagetransform['rotation'] == 90:
			offset['x'] = camerasize['y']/binning['y'] - offset['y'] - dimension['y']
			offset['y'] = offset['x']
		elif imagetransform['rotation'] == 180:
			offset['x'] = camerasize['x']/binning['x'] - offset['x'] - dimension['x']
			offset['y'] = camerasize['y']/binning['y'] - offset['y'] - dimension['y']
		elif imagetransform['rotation'] == 270:
			offset['x'] = offset['y']
			offset['y'] = camerasize['x']/binning['x'] - offset['x'] - dimension['x']

		hr = self.camera.Format(offset['x']*binning['x'], offset['y']*binning['y'],
														dimension['x'], dimension['y'],
														binning['x'], binning['y'])

		exposuretype = self.getExposureType()
		if exposuretype == 'normal':
			hr = self.camera.AcquireImage(self.getExposureTime(), 0)
		elif exposuretype == 'dark':
			hr = self.camera.AcquireDark(self.getExposureTime(), 0)
		elif exposuretype == 'bias':
			hr = self.camera.AcquireBias(0)
		elif exposuretype == 'readout':
			hr = self.camera.AcquireReadout(0)
		else:
			raise ValueError('invalid exposure type for image acquisition')

		imagesize = self.bytesperpixel*dimension['x']*dimension['y']

		map = mmapfile.mmapfile('', self.mmname, imagesize)
		#na = numarray.array(array.array(self.arraytypecode, map.read(imagesize)),
		#										self.imagetype)
		na = numarray.fromstring(map.read(imagesize), self.imagetype)
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

	def getImageTransform(self):
		bitmask = self._getParameterValue('cpImageGeometry')

		mirror = []
		if bitmask & 1: # mirrored horizontal
			mirror.append('horizontal')
		if bitmask & 2: # mirrored vertical
			mirror.append('vertical')

		rotation = 0
		if bitmask & 4: # rotated 90 degrees CCW
			rotation += 90
		if bitmask & 8: # rotated 180 degrees
			rotation += 180
		if bitmask & 16: # rotated 90 degrees CW
			rotation += 270
		rotation %= 360

		return {'mirror': mirror, 'rotation': rotation}

	def setImageTransform(self, value):
		# {'type': dict,
		#		'values': {'mirror':
		#								{'type': str, 'values': ['horizontal', 'vertical']},
		#							'rotation':
		#								{'type': int,	'values': [0, 90, 180, 270]}}}
		bitmask = 0

		if 'horizontal' in value['mirror']:
			bitmask |= 1
		if 'vertical' in value['mirror']:
			bitmask |= 2

		if value['rotation'] == 90:
			bitmask |= 4
		if value['rotation'] == 180:
			bitmask |= 8
		if value['rotation'] == 270:
			bitmask |= 16

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
	except NameError:
		pass
	mmname = 'CAM_PXL_DATA'
	def __init__(self):
		ccdcamera.CCDCamera.__init__(self)
		Tietz.__init__(self)
	
class TietzSimulation(Tietz, ccdcamera.CCDCamera):
	name = 'Tietz Simulation'
	try:
		cameratype = win32com.client.constants.ctSimulation
	except NameError:
		pass
	mmname = 'CAM_SIMU_DATA'
	def __init__(self):
		ccdcamera.CCDCamera.__init__(self)
		Tietz.__init__(self)

class TietzPVCam(Tietz, ccdcamera.CCDCamera):
	name = 'Tietz PVCam'
	try:
		cameratype = win32com.client.constants.ctPVCam
	except NameError:
		pass
	mmname = 'CAM_PVCAM_DATA'
	def __init__(self):
		ccdcamera.CCDCamera.__init__(self)
		Tietz.__init__(self)
	
class TietzFastScan(Tietz, ccdcamera.CCDCamera):
	name = 'Tietz FastScan'
	try:
		cameratype = win32com.client.constants.ctFastScan
	except NameError:
		pass
	mmname = 'CAM_FASTSCAN_DATA'
	def __init__(self):
		ccdcamera.CCDCamera.__init__(self)
		Tietz.__init__(self)
	
class TietzFastScanFW(Tietz, ccdcamera.CCDCamera):
	name = 'Tietz FastScan Firewire'
	try:
		cameratype = win32com.client.constants.ctF114_FW
	except NameError:
		pass
	mmname = 'CAM_FSFW_DATA'
	def __init__(self):
		ccdcamera.CCDCamera.__init__(self)
		Tietz.__init__(self)
	
class TietzSCX(Tietz, ccdcamera.CCDCamera):
	name = 'Tietz SCX'
	try:
		cameratype = win32com.client.constants.ctSCX
	except NameError:
		pass
	mmname = 'CAM_SCX_DATA'
	def __init__(self):
		ccdcamera.CCDCamera.__init__(self)
		Tietz.__init__(self)

