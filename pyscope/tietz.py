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
	foo = tietz()
	result = foo.getImage({'x': 0, 'y': 0}, {'x': 128, 'y': 128}, {'x': 1, 'y': 1}, 500.0)
	print result
