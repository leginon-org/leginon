import camera
import sys

if sys.platform != 'win32':
	class tietz(camera.camera):
		def __init__(self):
			pass
else:
	import win32com.client
	import tietzcom
	import mmapfile
	import array
	import Numeric
	import time
	
	class tietz(camera.camera):
		hCam = None
		camType = None
		
		def __init__(self):
			camera.camera.__init__(self)
			try:
				self.theCamera = win32com.client.Dispatch("CAMC.Camera")		
			except:
				print "Error: cannot dispatch CAMC.Camera"
				raise
	
			#self.camType = win32com.client.constants.ctSimulation
			self.camType = win32com.client.constants.ctPXL
			#self.camType = win32com.client.constants.ctPVCam
			#self.camType = win32com.client.constants.ctFastScan
	
			try:
				self.hCam = self.theCamera.Initialize(self.camType, 0)
			except:
				print "Error: camera COM object already intialized"
				raise

			self.arraytypecode = 'H'
			self.Numerictypecode = Numeric.UInt16

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

if __name__ == '__main__':
	foo = tietz()
	result = foo.getImage({'x': 0, 'y': 0}, {'x': 128, 'y': 128}, {'x': 1, 'y': 1}, 500)
	print result
