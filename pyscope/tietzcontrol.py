import threading
import pythoncom
import pywintypes
import win32com.client

class CameraControl(object):
	def __init__(self):
		self.pingname = 'pyscope'
		self.cameralock = threading.RLock()
		self.camera = None
		self.cameras = []

	def addCamera(self, camera):
		self.lock()
		if camera in self.cameras:
			self.unlock()
			raise ValueError

		if not self.cameras:
			try:
				self.initialize()
			except:
				self.unlock()
				raise

		camera.setCameraType()

		try:
			hr = cameracontrol.camera.Initialize(camera.cameratype, 0)
		except pywintypes.com_error, e:
			self.unlock()
			raise RuntimeError('error initializing camera')
		except:
			self.unlock()
			raise

		self.cameras.append(camera)
		self.unlock()

	def removeCamera(self, camera):
		self.lock()
		self.cameras.remove(camera)

		if not self.cameras:
			try:
				self.uninitialize()
			except:
				self.unlock()
				raise

		self.unlock()

	def setCamera(self, camera):
		self.camera.ActiveCamera = camera.cameratype

	def lock(self):
		self.cameralock.acquire()

	def unlock(self):
		self.cameralock.release()

	def initialize(self):
		pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)

		try:
			self.camera = win32com.client.Dispatch('CAMC4.Camera')		
		except pywintypes.com_error, e:
			raise RuntimeError('failed to initialize interface CAMC4.Camera')

		try:
			ping = win32com.client.Dispatch('pyscope.CAMCCallBack')
		except pywintypes.com_error, e:
			raise RuntimeError('failed to initialize interface pyscope.Ping')

		try:
			hr = self.camera.RegisterCAMCCallBack(ping, self.pingname)
		except pywintypes.com_error, e:
			raise RuntimeError('error registering callback COM object')

		hr = self.camera.RequestLock()
		if hr == win32com.client.constants.crDeny:
			raise RuntimeError('error locking camera, denied lock')
		elif hr == win32com.client.constants.crBusy:
			raise RuntimeError('error locking camera, camera busy')
		elif hr == win32com.client.constants.crSucceed:
			pass

	def uninitialize(self):
		self.camera.UnlockCAMC()

cameracontrol = CameraControl()
