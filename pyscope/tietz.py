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
	import base64
	import array
	
	class tietz(camera.camera):
		hCam = None
		camType = None
		
		def __init__(self):
			self.theCamera = win32com.client.Dispatch("CAMC.Camera")		
	
			self.camType = win32com.client.constants.ctSimulation
			#self.camType = win32com.client.constants.ctPXL
			#self.camType = win32com.client.constants.ctPVCam
			#self.camType = win32com.client.constants.ctFastScan
	
			self.hCam = self.theCamera.Initialize(self.camType, 0)
		
		def __del__(self):
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
	
			map = mmapfile.mmapfile(mmname, size)
			result = map.read(size)
			map.close()
			#return base64.encodestring(result)
			return result
	
		def getImage(self, xOff, yOff, xDim, yDim, xBin, yBin, expTime, type):	
			# 0 uses internal flash signal
			# 1 uses internal exposure signal (PVCam and PXL only)
			shutterMode = 1
			bytesPerPixel = 2
	
			self.theCamera.Format(self.hCam, xOff, yOff, xDim, yDim, xBin, yBin)
	
			if type == "illuminated":
				self.theCamera.AcquireImage(self.hCam, expTime, shutterMode, 0)
			elif type == "dark":
				self.theCamera.AcquireDark(self.hCam, expTime, 0)
			else:
				raise ValueError
	
			return self.mmapImage(bytesPerPixel*xDim*yDim)
		
