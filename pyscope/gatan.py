import camera
import sys

if sys.platform != 'win32':
	class gatan(camera.camera):
		def __init__(self):
			pass
else:
	import win32com.client
	import gatancom
	import base64
	import array
	import Numeric

	class gatan(camera.camera):
		def __init__(self):
			self.theCamera = win32com.client.Dispatch("TecnaiCCD.GatanCamera")        
			self.arraytypecode = 'H'
			self.Numerictypecode = Numeric.UInt16
	    
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
	
			imagetuple = self.theCamera.AcquireRawImage()

			imagelist = []
			for row in imagetuple:
				for value in row:
					imagelist.append(value)
			a = array.array(self.arraytypecode, imagelist)
			na = Numeric.array(a, self.Numerictypecode)
			na.shape = (dimension['y'], dimension['x'])
			return na
	    
