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
			self.theCamera.ExposureTime = exposure_time / 1000
	
			if type == "illuminated":
				imagetuple = self.theCamera.AcquireRawImage()
			elif type == "dark":
				tmpExpTime = self.theCamera.ExposureTime
				self.theCamera.ExposureTime = 0
				imagetuple = self.theCamera.AcquireImage()
				self.theCamera.ExposureTime = tmpExpTime
			else:
				raise ValueError
			imagelist = []
			for row in imagetuple:
				for value in row:
					imagelist.append(value)
			a = array.array(self.arraytypecode, imagelist)
			na = Numeric.array(a, self.Numerictypecode)
			return Numeric.reshape(na, (dimension['y'], dimension['x']))
	    
