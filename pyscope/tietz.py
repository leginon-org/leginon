#
# COPYRIGHT:
#			 The Leginon software is Copyright 2003
#			 The Scripps Research Institute, La Jolla, CA
#			 For terms of the license agreement
#			 see	http://ami.scripps.edu/software/leginon-license
#
import camera
import sys

if sys.platform != 'win32':
	class Tietz(camera.Camera):
		def __init__(self):
			pass
else:
	sys.coinit_flags = 0
	import pythoncom
	import pywintypes
	import win32com.client
	import tietzcom
	import mmapfile
	import array
	import Numeric
	import time

	class Ping:
		_typelib_guid_ = tietzcom.CLSID
		_com_interfaces_ = ['ICAMCCallBack']
		_public_methods_ = ['LivePing', 'RequestLock']
		_reg_clsid_ = '{CB1473AA-6F1E-4744-8EFD-68F91CED4294}'
		_reg_progid_ = 'PythonCAMC4.Ping'

		def LivePing(self):
			return 0

		def RequestLock(self):
			print 'RequestLock'
			return False

	class Tietz(camera.Camera):
		camType = None

		dependencymapping = {
			'getChipName': [('cpChipName', 'r')],
			'getCameraName': [('cpCameraName', 'r')],
			'getCameraSize': [('cpTotalDimensionX', 'r'),
														('cpTotalDimensionY', 'r')],
			'getPixelSize': [('cpPixelSizeX', 'r'),
													('cpPixelSizeY', 'r')],
			'getMaximumPixelValue': [('cpDynamic', 'r')],
			'getNumberOfGains': [('cpNumberOfGains', 'r')],
			'getGainFactors': [('cpGainFactors', 'r')],
			'getNumberOfReadoutSpeeds': [('cpNumberOfReadoutSpeeds', 'r')],
			'getReadoutSpeeds': [('cpReadoutSpeeds', 'r')],
			'getLiveModeAvailable': [('cpLiveModeAvailable', 'r')],
			'getNumberOfDeadColumns': [('cpNumberOfDeadColumns', 'r')],
			'getDeadColumns': [('cpDeadColumns', 'r')],
			'getSimulationImagePath': [('cpImagePath', 'r')],
			'getGain': [('cpCurrentGainIndex', 'r'), ('cpGainFactors', 'r')],
			'getGainIndex': [('cpCurrentGainIndex', 'r')],
			'setGainIndex': [('cpCurrentGainIndex', 'w')],
			'getReadoutSpeed': [('cpCurrentSpeedIndex', 'r'),
															('cpReadoutSpeeds', 'r')],
			'getReadoutSpeedIndex': [('cpCurrentSpeedIndex', 'r')],
			'setReadoutSpeedIndex': [('cpCurrentSpeedIndex', 'w')],
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
			'setUseSpeedtabForGainSwitch': [('cpUseSpeedtabForGainSwitch', 'w')],
		}
		
		def __init__(self, cameratype=None):
			# ???
			import win32com.client
			camera.Camera.__init__(self)

			self.arraytypecode = 'H'
			self.Numerictypecode = Numeric.UInt16

			pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)
			try:
				self.theCamera = win32com.client.Dispatch("CAMC4.Camera")		
			except pywintypes.com_error, e:
				print "Error dispatching CAMC4.Camera"
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
				hr = self.theCamera.RegisterCAMCCallBack(ping, 'EM')
			except pywintypes.com_error, e:
				print 'Error registering callback'
				print e
				return

			hr = self.theCamera.RequestLock()
			if hr == win32com.client.constants.crDeny:
				print 'Error locking camera, denied lock'
				return
			elif hr == win32com.client.constants.crBusy:
				print 'Error locking camera, camera busy'
				return
			elif hr == win32com.client.constants.crSucceed:
				pass
	
			if cameratype is None or cameratype == 'PXL':
				self.camType = win32com.client.constants.ctPXL
			elif cameratype == 'Simulation':
				self.camType = win32com.client.constants.ctSimulation
			elif cameratype == 'PVCam':
				self.camType = win32com.client.constants.ctPVCam
			elif cameratype == 'FastScan':
				self.camType = win32com.client.constants.ctFastScan
			elif cameratype == 'FastScanFW':
				self.camType = win32com.client.constants.ctF114_FW
			elif cameratype == 'SCX':
				self.camType = win32com.client.constants.ctSCX
			else:
				raise ValueError('Invalid camera type specified')
	
			try:
				hr = self.theCamera.Initialize(self.camType, 0)
			except pywintypes.com_error, e:
				print "Error initializing camera"
				print e
				return

			for methodname, dependencies in self.dependencymapping.items():
				supported = True
				for dependency in dependencies:
					parametername, permission = dependency
					if permission not in self.getPermissions(parametername):
						supported = False
				if not supported:
					setattr(self, methodname, self.raiseNotImplementedError)

		def raiseNotImplementedError(self, **kwargs):
			raise NotImplementedError

		def getPermissions(self, parametername):
			try:
				parameter = getattr(win32com.client.constants, parametername)
			except:
				return ''
			value = self.theCamera.QueryParameter(parameter)
			if value == 0:
				return ''
			elif value == 5:
				return 'r'
			elif value == 6:
				return 'w'
			elif value == 7:
				return 'rw'
			elif value == 9:
				return 'r'
			elif value == 10:
				return 'w'
			elif value == 11:
				return 'rw'
			else:
				return ''

		def exit(self):
			self.theCamera.UnlockCAMC()
	
		def mmapImage(self, size):
			if self.camType == win32com.client.constants.ctSimulation:
				mmname = "CAM_SIMU_DATA"
			elif self.camType == win32com.client.constants.ctPXL:
				mmname = "CAM_PXL_DATA"
			elif self.camType == win32com.client.constants.ctPVCam:
				mmname = "CAM_PVCAM_DATA"
			elif self.camType == win32com.client.constants.ctFastScan:
				mmname = "CAM_FASTSCAN_DATA"
			elif self.camType == win32com.client.constants.ctF114_FW:
				mmname = "CAM_FSFW_DATA"
			elif self.camType == win32com.client.constants.ctSCX:
				mmname = "CAM_SCX_DATA"
			else:
				raise ValueError
	
			map = mmapfile.mmapfile('', mmname, size)
			result = map.read(size)
			map.close()
			return result
	
		def getImage(self, offset, dimension, binning, exposure_time, imagetype):	
			# 0 uses internal flash signal
			# 1 uses internal exposure signal (PVCam and PXL only)
			shutter_mode = 1
			bytes_per_pixel = 2
	
			hr = self.theCamera.Format(offset['x'], offset['y'],
																	dimension['x'], dimension['y'],
																	binning['x'], binning['y'])
			if imagetype == 'normal':
				acquiremethod = self.theCamera.AcquireImage
			elif imagetype == 'dark':
				acquiremethod = self.theCamera.AcquireDark
			else:
				raise ValueError('Invalid image type')

			hr = acquiremethod(exposure_time, 0)

			a = array.array(self.arraytypecode, self.mmapImage(
																bytes_per_pixel*dimension['x']*dimension['y']))
			na = Numeric.array(a, self.Numerictypecode)
			return Numeric.reshape(na, (dimension['y'], dimension['x']))

		def setInserted(self, value):
			pass

		def getInserted(self):
			return True

		def getChipName(self):
			return self.theCamera.SParam(win32com.client.constants.cpChipName)

		def getCameraName(self):
			return self.theCamera.SParam(win32com.client.constants.cpCameraName)

		def getCameraSize(self):
			x = self.theCamera.LParam(win32com.client.constants.cpTotalDimensionX)
			y = self.theCamera.LParam(win32com.client.constants.cpTotalDimensionY)
			return {'x': x, 'y': y}

		def getPixelSize(self):
			x = self.theCamera.LParam(win32com.client.constants.cpPixelSizeX)
			y = self.theCamera.LParam(win32com.client.constants.cpPixelSizeY)
			return {'x': x/1000000000.0, 'y': y/1000000000.0}

		def getMaximumPixelValue(self):
			return self.theCamera.LParam(win32com.client.constants.cpDynamic)

		def getNumberOfGains(self):
			return self.theCamera.LParam(win32com.client.constants.cpNumberOfGains)

		def getGainFactors(self):
			string = self.theCamera.SParam(win32com.client.constants.cpGainFactors)
			return eval(string)

		def getNumberOfReadoutSpeeds(self):
			return self.theCamera.LParam(
															win32com.client.constants.cpNumberOfReadoutSpeeds)

		def getReadoutSpeeds(self):
			string = self.theCamera.SParam(win32com.client.constants.cpReadoutSpeeds)
			return eval(string)

		def getLiveModeAvailable(self):
			value = self.theCamera.LParam(	
																	win32com.client.constants.cpLiveModeAvailable)
			if value == 1:
				return True
			elif value == 0:
				return False
			raise RuntimeError('Unknown live mode available value')

		def getNumberOfDeadColumns(self):
			return self.theCamera.LParam(
																win32com.client.constants.cpNumberOfDeadColumns)

		def getDeadColumns(self):
			string = self.theCamera.SParam(win32com.client.constants.cpDeadColumns)
			return eval(string)

		def getSimulationImagePath(self):
			return self.theCamera.SParam(win32com.client.constants.cpImagePath)

		def getGainIndex(self):
			return self.theCamera.LParam(win32com.client.constants.cpCurrentGainIndex)

		def getGain(self):
			return self.getGainFactors()[self.getGainIndex() - 1]

		def setGainIndex(self, value):
			try:
				self.theCamera.SetLParam(win32com.client.constants.cpCurrentGainIndex,
																	value)
			except pywintypes.com_error:
				raise ValueError('Invalid gain index specified')

		def getReadoutSpeedIndex(self):
			return self.theCamera.LParam(
																	win32com.client.constants.cpCurrentSpeedIndex)

		def getReadoutSpeed(self):
			return self.getReadoutSpeeds()[self.getReadoutSpeedIndex() - 1]

		def setReadoutSpeedIndex(self, value):
			try:
				self.theCamera.SetLParam(win32com.client.constants.cpCurrentSpeedIndex,
																	value)
			except pywintypes.com_error:
				raise ValueError('Invalid readout speed index specified')

		def getImageTransform(self):
			bitmask = self.theCamera.LParam(win32com.client.constants.cpImageGeometry)

			mirror = []
			if bitmask & 1:
				mirror.append('horizontal')
				# mirrored horizontal
			if bitmask & 2:
				# mirrored vertical
				mirror.append('vertical')

			rotation = 0
			if bitmask & 4:
				# rotated 90 degrees CCW
				rotation += 90
			if bitmask & 8:
				# rotated 180 degrees
				rotation += 180
			if bitmask & 16:
				# rotated 90 degrees CW
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
			if value['roration'] == 180:
				bitmask |= 8
			if value['rotation'] == 270:
				bitmask |= 16

			self.theCamera.SetLParam(win32com.client.constants.cpImageGeometry,
																bitmask)

		def getTemperature(self):
			value = self.theCamera.LParam(
																win32com.client.constants.cpCurrentTemperature)
			return value/1000.0

		def setTemperature(self, value):
			value = int(value*1000)
			self.theCamera.SetLParam(win32com.client.constants.cpTemperatureSetpoint,
																value)

		def getShutterOpenDelay(self):
			return self.theCamera.LParam(win32com.client.constants.cpShutterOpenDelay)

		def setShutterOpenDelay(self, value):
			try:
				self.theCamera.SetLParam(win32com.client.constants.cpShutterOpenDelay,
															value)
			except pywintypes.com_error:
				raise ValueError('Invalid shutter open delay')

		def getShutterCloseDelay(self):
			return self.theCamera.LParam(
																	win32com.client.constants.cpShutterCloseDelay)

		def setShutterCloseDelay(self, value):
			try:
				self.theCamera.SetLParam(win32com.client.constants.cpShutterCloseDelay,
															value)
			except pywintypes.com_error:
				raise ValueError('Invalid shutter close delay')

		def getSerialNumber(self):
			return self.theCamera.SParam(win32com.client.constants.cpSerialNumber)
			
		def getPreampDelay(self):
			value = self.theCamera.LParam(win32com.client.constants.cpPreampDelay)
			return value/1000.0

		def setPreampDelay(self, value):
			value = int(value*1000)
			try:
				self.theCamera.SetLParam(win32com.client.constants.cpPreampDelay, value)
			except pywintypes.com_error:
				raise ValueError('Invalid preamp delay')

		# PMode boolean?
		def getParallelMode(self):
			return self.theCamera.LParam(win32com.client.constants.cpPMode)

		# PMode boolean?
		def setParallelMode(self, value):
			try:
				self.theCamera.SetLParam(win32com.client.constants.cpPMode, value)
			except pywintypes.com_error:
				raise ValueError('Invalid parallel mode')

		def setUseSpeedtabForGainSwitch(self, value):
			if value:
				value = 1
			else:
				value = 0
			self.theCamera.SetLParam(
									win32com.client.constants.cpUseSpeedtabForGainSwitch, value)

		def getHardwareGainIndex(self):
			return self.theCamera.LParam(win32com.client.constants.cpHWGainIndex)

		def getHardwareSpeedIndex(self):
			return self.theCamera.LParam(win32com.client.constants.cpHWSpeedIndex)

		def getRetractable(self):
			value = self.theCamera.LParam(win32com.client.constants.cpIsRetractable)
			if value:
				return True
			else:
				return False

		def getCameraAxis(self):
			value = self.theCamera.LParam(
																win32com.client.constants.cpCameraPositionOnTem)
			if value == 0:
				return 'on'
			elif value == 1:
				return 'off'
			else:
				return 'unknown'

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
	
if __name__ == '__main__':
	foo = TietzSimulation()
	#foo = TietzSCX()
	methods = dir(foo)
	methods.remove('getImage')
	methods.remove('getPermissions')
	for i in methods:
		if i[:3] == 'get':
			try:
				print i, getattr(foo, i)()
			except NotImplementedError:
				print 'not implemented'
#	for i in methods:
#		if i[:3] == 'set':
#			print i

