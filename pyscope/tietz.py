#
# COPYRIGHT:
#      The Leginon software is Copyright 2003
#      The Scripps Research Institute, La Jolla, CA
#      For terms of the license agreement
#      see  http://ami.scripps.edu/software/leginon-license
#

import sys
sys.coinit_flags = 0
import pythoncom
import pywintypes
import win32com.client
import array
import mmapfile
import Numeric
import tietzcom

class Ping:
	_typelib_guid_ = tietzcom.CLSID
	_com_interfaces_ = ['ICAMCCallBack']
	_public_methods_ = ['LivePing', 'RequestLock']
	_reg_clsid_ = '{CB1473AA-6F1E-4744-8EFD-68F91CED4294}'
	_reg_progid_ = 'PythonCAMC4.Ping'

	def LivePing(self):
		return 0

	def RequestLock(self):
		return False

class Tietz(object):
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

	def __init__(self, cameratypename):
		self.unsupported = []
		self.arraytypecode = 'H'
		self.numerictypecode = Numeric.UInt16
		self.bytesperpixel = 2

		self.binning = {'x': 1, 'y': 1}
		self.offset = {'x': 0, 'y': 0}
		self.dimension = {'x': 512, 'y': 512}
		self.exposuretime = 500
		self.exposuretype = 'normal'

		# ???
		import win32com.client

		pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)
		try:
			self.camera = win32com.client.Dispatch('CAMC4.Camera')		
		except pywintypes.com_error, e:
			print 'Error dispatching CAMC4.Camera'
			print e
			return

		try:
			ping = win32com.client.Dispatch('PythonCAMC4.Ping')
		except pywintypes.com_error, e:
			import win32com.server.register
			win32com.server.register.UseCommandLine(Ping)
			try:
				ping = win32com.client.Dispatch('PythonCAMC4.Ping')
			except pywintypes.com_error, e:
				print 'Error dispatching callback COM object'
				print e
				return

		try:
			hr = self.camera.RegisterCAMCCallBack(ping, 'EM')
		except pywintypes.com_error, e:
			print 'Error registering callback'
			print e
			return

		hr = self.camera.RequestLock()
		if hr == win32com.client.constants.crDeny:
			print 'Error locking camera, denied lock'
			return
		elif hr == win32com.client.constants.crBusy:
			print 'Error locking camera, camera busy'
			return
		elif hr == win32com.client.constants.crSucceed:
			pass

		if cameratypename == 'PXL':
			cameratype = win32com.client.constants.ctPXL
			self.mmname = 'CAM_PXL_DATA'
		elif cameratypename == 'Simulation':
			cameratype = win32com.client.constants.ctSimulation
			self.mmname = 'CAM_SIMU_DATA'
		elif cameratypename == 'PVCam':
			cameratype = win32com.client.constants.ctPVCam
			self.mmname = 'CAM_PVCAM_DATA'
		elif cameratypename == 'FastScan':
			cameratype = win32com.client.constants.ctFastScan
			self.mmname = 'CAM_FASTSCAN_DATA'
		elif cameratypename == 'FastScanFW':
			cameratype = win32com.client.constants.ctF114_FW
			self.mmname = 'CAM_FSFW_DATA'
		elif cameratypename == 'SCX':
			cameratype = win32com.client.constants.ctSCX
			self.mmname = 'CAM_SCX_DATA'
		else:
			raise ValueError('Invalid camera type specified')
	
		try:
			hr = self.camera.Initialize(cameratype, 0)
		except pywintypes.com_error, e:
			print 'Error initializing camera'
			print e
			return

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
	
	def mmapImage(self, size):
		map = mmapfile.mmapfile('', self.mmname, size)
		result = map.read(size)
		map.close()
		return result

	def getOffset(self):
		return self.offset

	def setOffset(self, value):
		self.offset = value

	def getDimension(self):
		return self.dimension

	def setDimension(self, value):
		self.dimension = value

	def getBinning(self):
		return self.binning

	def setBinning(self, value):
		self.binning = value

	def getExposureTime(self):
		return self.exposuretime

	def setExposureTime(self, value):
		self.exposuretime = value

	def getExposureType(self):
		return self.exposuretype

	def setExposureType(self, value):
		if value not in ['normal', 'dark']:
			raise ValueError('Invalid exposure type')
		self.exposuretype = value
	
	def getImage(self):
		# 0 uses internal flash signal
		# 1 uses internal exposure signal (PVCam and PXL only)
		# shutter_mode = 1

		offset = self.getOffset()
		dimension = self.getDimension()
		binning = self.getBinning()
		hr = self.camera.Format(offset['x'], offset['y'], dimension['x'],
																dimension['y'], binning['x'], binning['y'])

		exposuretype = self.getExposureType()
		if exposuretype == 'normal':
			acquiremethod = self.camera.AcquireImage
		elif exposuretype == 'dark':
			acquiremethod = self.camera.AcquireDark

		hr = acquiremethod(self.getExposureTime(), 0)

		imagesize = self.bytesperpixel*dimension['x']*dimension['y']
		# Numeric directly?
		a = array.array(self.arraytypecode, self.mmapImage(imagesize))
		na = Numeric.array(a, self.numerictypecode)
		na.shape = (dimension['y'], dimension['x'])
		return na
		#return Numeric.reshape(na, (dimension['y'], dimension['x']))

	def getChipName(self):
		return self._getParameterValue('cpChipName')

	def getCameraName(self):
		return self._getParameterValue('cpCameraName')

	def getCameraSize(self):
		x = self._getParameterValue('cpTotalDimensionX')
		y = self._getParameterValue('cpTotalDimensionY')
		return {'x': x, 'y': y}

	def getPixelSize(self):
		x = self._getParameterValue('cpPixelSizeX')/1000000000.0
		y = self._getParameterValue('cpPixelSizeY')/1000000000.0
		return {'x': x, 'y': y}

	def getMaximumPixelValue(self):
		return self._getParameterValue('cpDynamic')

	def getNumberOfGains(self):
		return self._getParameterValue('cpNumberOfGains')

	# eval...
	def getGainFactors(self):
		return eval(self._getParameterValue('cpGainFactors'))

	def getNumberOfSpeeds(self):
		return self._getParameterValue('cpNumberOfSpeeds')

	# eval...
	def getSpeeds(self):
		return eval(self._getParameterValue('cpSpeeds'))

	def getLiveModeAvailable(self):
		value = self._getParameterValue('cpLiveModeAvailable')
		if value == 1:
			return True
		elif value == 0:
			return False
		raise RuntimeError('Unknown live mode available value')

	def getNumberOfDeadColumns(self):
		return self._getParameterValue('cpNumberOfDeadColumns')

	# eval...
	def getDeadColumns(self):
		return eval(self._getParameterValue('cpDeadColumns'))

	def getSimulationImagePath(self):
		return self._getParameterValue('cpImagePath')

	def getGainIndex(self):
		return self._getParameterValue('cpCurrentGainIndex')

	def getGain(self):
		return self.getGainFactors()[self.getGainIndex() - 1]

	def setGainIndex(self, value):
		try:
			self._setParameterValue('cpCurrentGainIndex', value)
		except pywintypes.com_error:
			raise ValueError('Invalid gain index specified')

	def getSpeedIndex(self):
		return self._getParameterValue('cpCurrentSpeedIndex')

	def getSpeed(self):
		return self.getSpeeds()[self.getSpeedIndex() - 1]

	def setSpeedIndex(self, value):
		try:
			self._setParameterValue('cpCurrentSpeedIndex', value)
		except pywintypes.com_error:
			raise ValueError('Invalid speed index specified')

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
		self._setParameterValue('cpTemperatureSetpoint', int(value*1000))

	def getShutterOpenDelay(self):
		return self._getParameterValue('cpShutterOpenDelay')

	def setShutterOpenDelay(self, value):
		try:
			self._setParameterValue('cpShutterOpenDelay', value)
		except pywintypes.com_error:
			raise ValueError('Invalid shutter open delay')

	def getShutterCloseDelay(self):
		return self._getParameterValue('cpShutterCloseDelay')

	def setShutterCloseDelay(self, value):
		try:
			self._setParameterValue('cpShutterCloseDelay', value)
		except pywintypes.com_error:
			raise ValueError('Invalid shutter close delay')

	def getSerialNumber(self):
		return self._getParameterValue('cpSerialNumber')
			
	def getPreampDelay(self):
		return self._getParameterValue('cpPreampDelay')/1000.0

	def setPreampDelay(self, value):
		try:
			self._setParameterValue('cpPreampDelay', int(value*1000))
		except pywintypes.com_error:
			raise ValueError('Invalid preamp delay')

	# PMode boolean?
	def getParallelMode(self):
		return self._getParameterValue('cpPMode')

	def setParallelMode(self, value):
		try:
			self._setParameterValue('cpPMode', value)
		except pywintypes.com_error:
			raise ValueError('Invalid parallel mode')

	def setUseSpeedTableForGainSwitch(self, value):
		if value:
			value = 1
		else:
			value = 0
		self._setParameterValue('cpUseSpeedtabForGainSwitch', value)

	def getHardwareGainIndex(self):
		return self._getParameterValue('cpHWGainIndex')

	def getHardwareSpeedIndex(self):
		return self._getParameterValue('cpHWSpeedIndex')

	def getRetractable(self):
		value = self._getParameterValue('cpIsRetractable')
		if value:
			return True
		else:
			return False

	def getCameraAxis(self):
		value = self._getParameterValue('cpCameraPositionOnTem')
		if value == 0:
			return 'on'
		elif value == 1:
			return 'off'
		else:
			raise RuntimeError('Error getting camera axis')

class TietzPXL(Tietz):
	def __init__(self):
		Tietz.__init__(self, 'PXL')
	
class TietzSimulation(Tietz):
	def __init__(self):
		Tietz.__init__(self, 'Simulation')

class TietzPVCam(Tietz):
	def __init__(self):
		Tietz.__init__(self, 'PVCam')
	
class TietzFastScan(Tietz):
	def __init__(self):
		Tietz.__init__(self, 'FastScan')
	
class TietzFastScanFW(Tietz):
	def __init__(self):
		Tietz.__init__(self, 'FastScanFW')
	
class TietzSCX(Tietz):
	def __init__(self):
		Tietz.__init__(self, 'SCX')

