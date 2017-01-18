from leginon import leginondata
import threading
import time

# Change this to False to avoid automated screen lifting
AUTO_SCREEN_UP = True
AUTO_COLUMN_VALVE_OPEN = True

default_settings = leginondata.CameraSettingsData()
default_settings['dimension'] = {'x': 1024, 'y': 1024}
default_settings['offset'] = {'x': 0, 'y': 0}
default_settings['binning'] = {'x': 1, 'y': 1}
default_settings['exposure time'] = 200
default_settings['save frames'] = False
default_settings['frame time'] = 200
default_settings['align frames'] = False
default_settings['align filter'] = 'None'
default_settings['use frames'] = ''
default_settings['readout delay'] = 0

class CameraClient(object):
	def __init__(self):
		self.exposure_start_event = threading.Event()
		self.exposure_done_event = threading.Event()
		self.readout_done_event = threading.Event()
		self.position_camera_done_event = threading.Event()

	def clearCameraEvents(self):
		self.exposure_start_event.clear()
		self.exposure_done_event.clear()
		self.readout_done_event.clear()
		self.position_camera_done_event.clear()

	def waitExposureDone(self):
		self.exposure_done_event.wait()

	def waitReadoutDone(self):
		self.readout_done_event.wait()

	def waitPositionCameraDone(self):
		self.position_camera_done_event.wait()

	def startExposureTimer(self):
		'''
		We want to approximate when the CCD exposure is done,
		but not wait for the readout, which can take a lot longer.
		This will set a timer that will generate an event when
		we think the exposure should be done.
		'''
		extratime = 1.0
		self.logger.debug('Extra time for exposure: %s (tune this lower to save time)' % (extratime,))
		exposure_seconds = self.instrument.ccdcamera.ExposureTime / 1000.0
		waittime = exposure_seconds + extratime
		t = threading.Timer(waittime, self.exposure_done_event.set)
		self.exposure_start_event.set()
		t.start()

	def protectSpecimen(self,status):
		if not self.instrument.tem.BeamBlankedDuringCameraExchange or len(self.instrument.ccdcameras) < 2:
			return
		if status not in ('on','off'):
			return
		self.logger.info('Turn %s beam blanker' % (status,))
		self.instrument.tem.BeamBlank = status

	def positionCamera(self,camera_name=None, allow_retracted=False):
		'''
		Position the camera ready for acquisition
		'''
		orig_camera_name = self.instrument.getCCDCameraName()
		if camera_name is not None:
			self.instrument.setCCDCamera(camera_name)
			orig_camera_name = camera_name
		else:
			camera_name = orig_camera_name
			

		camera_exchanged = False
		orig_blank_status = self.instrument.tem.BeamBlank
		fakek2cam = None

		hosts = map((lambda x: self.instrument.ccdcameras[x].Hostname),self.instrument.ccdcameras.keys())
		## Retract the cameras that are above this one (higher zplane)
		## or on the same host but lower because the host often
		## retract the others regardless of the position but not include
		## that in the timing.  Often get blank image as a result
		for name,cam in self.instrument.ccdcameras.items():
			if 'FakeK2' == name and camera_name is not None and 'GatanK2' in camera_name:
				## With current camera control on TUI/TIA, K2 behind Falcon can not shutter
				## unless an unused camera (TIA-Orius) is inserted.
				## Here it sets the fake camera
				fakek2cam = cam
				continue
			if cam.Zplane > self.instrument.ccdcamera.Zplane or (hosts.count(cam.Hostname) > 1 and cam.Zplane < self.instrument.ccdcamera.Zplane):
				try:
					if cam.Inserted:
						self.protectSpecimen('on')
						camera_exchanged = True
						cam.Inserted = False
						self.logger.info('retracted camera: %s' % (name,))
				except:
					pass

		# Insert fake camera for GatanK2
		if fakek2cam:
			fakek2cam.Inserted = True

		## insert the current camera, unless allow_retracted
		if not allow_retracted:
			try:
				inserted = self.instrument.ccdcamera.Inserted
			except:
				inserted = True
			if not inserted:
				camname = self.instrument.getCCDCameraName()
				self.logger.info('inserting camera: %s' % (camname,))
				self.instrument.ccdcamera.Inserted = True

		if camera_exchanged:
			self.protectSpecimen(orig_blank_status)

		if camera_name is not None:
			# set current camera back in case of side effect
			self.instrument.setCCDCamera(orig_camera_name)
		self.position_camera_done_event.set()

	def liftScreenBeforeExposure(self,exposure_type='normal'):
		'''
		Life main screen if it is down for non-dark exposure
		'''
		if exposure_type == 'dark':
			# Do not do anything if a dark image is about to be acquired
			return
		try:
			state = self.instrument.tem.MainScreenPosition
		except:
			state = 'down'
			pass
		if state != 'up':
			self.logger.info('Lifting screen for camera exposure....')
			self.instrument.tem.MainScreenPosition = 'up'

	def openColumnValveBeforeExposure(self,exposure_type='normal'):
		'''
		Open Column Valve if it is closed for non-dark exposure
		'''
		if exposure_type == 'dark':
			# Do not do anything if a dark image is about to be acquired
			return
		try:
			state = self.instrument.tem.ColumnValvePosition
		except:
			state = 'closed'
			pass
		if state != 'open':
			self.logger.info('Open Column Valve for camera exposure....')
			self.instrument.tem.ColumnValvePosition = 'open'

	def dummy(self):
		pass

	def prepareToAcquire(self,allow_retracted=False,exposure_type='normal'):
		t1 = threading.Thread(target=self.positionCamera(allow_retracted=allow_retracted))
		if AUTO_SCREEN_UP:
			t2 = threading.Thread(target=self.liftScreenBeforeExposure(exposure_type))
		else:
			t2 = threading.Thread(target=self.dummy())

		if AUTO_COLUMN_VALVE_OPEN:
			t3 = threading.Thread(target=self.openColumnValveBeforeExposure(exposure_type))
		else:
			t3 = threading.Thread(target=self.dummy())

		while t1.isAlive() or t2.isAlive() or t3.isAlive():
			time.sleep(0.5)

	def acquireCameraImageData(self, scopeclass=leginondata.ScopeEMData, allow_retracted=False, type='normal', force_no_frames=False):
		'''Acquire a raw image from the currently configured CCD camera'''
		self.prepareToAcquire(allow_retracted,exposure_type=type)
		if force_no_frames:
			try:
				self.instrument.ccdcamera.SaveRawFrames = False
			except TypeError:
				# some camera does not have this attribute
				pass
		## set type to normal or dark
		self.instrument.ccdcamera.ExposureType = type
		imagedata = leginondata.CameraImageData()
		imagedata['session'] = self.session

		## make sure shutter override is activated
		try:
			self.instrument.tem.ShutterControl = True
		except:
			# maybe tem has no such function
			pass

		## acquire image, get new scope/camera params
		try:
			scopedata = self.instrument.getData(scopeclass)
		except:
			raise
		#cameradata_before = self.instrument.getData(leginondata.CameraEMData)
		imagedata['scope'] = scopedata
		self.startExposureTimer()
		imagedata['image'] = self.instrument.ccdcamera.Image
		cameradata_after = self.instrument.getData(leginondata.CameraEMData)
		## only using cameradata_after, not cameradata_before
		imagedata['camera'] = cameradata_after

		## duplicating 'use frames' here because we may reuse same
		## CameraEMData for multiple versions of AcquisitionImageData
		imagedata['use frames'] = cameradata_after['use frames']

		self.readout_done_event.set()
		return imagedata
