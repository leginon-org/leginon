import camera
import sys

if sys.platform != 'win32':
	class gatan(camera.camera):
		def __init__(self):
			pass
else:
	import win32com.client
	import gatancom

	class gatan(camera.camera):
		def __init__(self):
			self.theCamera = win32com.client.Dispatch("TecnaiCCD.GatanCamera")        
	    
		def __del__(self):
			pass

		def getImage(self, offset, dimension, binning, exposure_time):    
			if binning['x'] != binning['y']:
				raise ValueError
			self.theCamera.CameraLeft = offset['x']
			self.theCamera.CameraRight = offset['x'] + dimension['x']
			self.theCamera.CameraTop = offset['y']
			self.theCamera.CameraBottom = offset['y'] + dimension['y']
			self.theCamera.Binning = binning['x']
			self.theCamera.ExposureTime = float(exposure_time) / 1000.0
	
			return self.theCamera.AcquireRawImage()
