#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
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
	import win32com.client
	import tietzcom
	import mmapfile
	import array
	import Numeric
	import time

	class Tietz(camera.Camera):
		hCam = None
		camType = None
		
		def __init__(self, cameratype=None):
			pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)
			camera.Camera.__init__(self)
			try:
				self.theCamera = win32com.client.Dispatch("CAMC.Camera")		
			except:
				print "Error: cannot dispatch CAMC.Camera"
				raise
	
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
				self.hCam = self.theCamera.Initialize(self.camType, 0)
			except:
				print "Error: camera COM object already intialized"
				raise

			self.arraytypecode = 'H'
			self.Numerictypecode = Numeric.UInt16
			self.camerasize = {'x': 2048, 'y': 2048}

		def exit(self):
			self.theCamera.Uninitialize(self.hCam)
	
		def mmapImage(self, size):
			if self.camType == win32com.client.constants.ctSimulation:
				mmname = "CAM_SIMU_DATA"
			elif self.camType == win32com.client.constants.ctPXL:
				mmname = "CAM_PXL_DATA"
			elif self.camType == win32com.client.constants.ctPVCam:
				mmname = "CAM_PVCAM_DATA"
			elif self.camType == win32com.client.constants.ctFastScan:
				mmname = "CAM_FASTSCAN_DATA"
			else:
				raise ValueError
	
			#map = mmapfile.mmapfile(mmname, size)
			map = mmapfile.mmapfile('', mmname, size)
			result = map.read(size)
			map.close()
			#return base64.encodestring(result)
			#return Numeric.reshape((selfNumeric.array(result, self.Numerictypecode)
			return result
	
		def getImage(self, offset, dimension, binning, exposure_time):	
			# 0 uses internal flash signal
			# 1 uses internal exposure signal (PVCam and PXL only)
			shutter_mode = 1
			bytes_per_pixel = 2
	
			self.theCamera.Format(self.hCam, offset['x'], offset['y'], \
														dimension['x'], dimension['y'], \
														binning['x'], binning['y'])
			self.theCamera.AcquireImage(self.hCam, exposure_time, shutter_mode, 0)
			a = array.array(self.arraytypecode, self.mmapImage(bytes_per_pixel*dimension['x']*dimension['y']))
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
