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

	class gatan(camera.camera):
		def __init__(self):
			self.theCamera = win32com.client.Dispatch("TecnaiCCD.GatanCamera")        
	    
		def __del__(self):
			pass
	
		def getImage(self, xOff, yOff, xDim, yDim, xBin, yBin, expTime, type):    
			if xBin != yBin:
				raise ValueError
			self.theCamera.CameraLeft = xOff
			self.theCamera.CameraRight = xOff + xDim
			self.theCamera.CameraTop = yOff
			self.theCamera.CameraBottom = yOff + yDim
			self.theCamera.Binning = xBin
			self.theCamera.ExposureTime = expTime / 1000
	
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
			image = array.array('H', imagelist)
			return base64.encodestring(image.tostring())
	        
	    
