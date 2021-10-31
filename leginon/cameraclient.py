from leginon import leginondata
import threading
import time

# Change this to False to avoid automated screen lifting
AUTO_SCREEN_UP = True
AUTO_COLUMN_VALVE_OPEN = True
# parallel imaging test
PARALLEL_IMAGING = False

default_settings = leginondata.CameraSettingsData()
default_settings['dimension'] = {'x': 1024, 'y': 1024}
default_settings['offset'] = {'x': 0, 'y': 0}
default_settings['binning'] = {'x': 1, 'y': 1}
default_settings['exposure time'] = 200
default_settings['save frames'] = False
default_settings['frame time'] = 200
default_settings['request nframes'] = 1
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
		'''
		Preparation before acquiring the image. Overwritable by subclasses
		such as MoveAcquisition to skip the real prepartion.
		'''
		try:
			self._prepareToAcquire(allow_retracted, exposure_type)
		except RuntimeError as e:
			# instrument emit RuntimeError through proxy
			self.logger.error(e)
		except Exception:
			raise

	def _prepareToAcquire(self,allow_retracted=False,exposure_type='normal'):
		'''
		Make sure the camera and scope is in the condition for acquiring
		the image.
		'''
		t1 = threading.Thread(target=self.positionCamera(allow_retracted=allow_retracted))
		if AUTO_SCREEN_UP:
			t2 = threading.Thread(target=self.liftScreenBeforeExposure(exposure_type))
		else:
			t2 = threading.Thread(target=self.dummy())

		if AUTO_COLUMN_VALVE_OPEN:
			t3 = threading.Thread(target=self.openColumnValveBeforeExposure(exposure_type))
		else:
			t3 = threading.Thread(target=self.dummy())

		if self.instrument.tem.ProjectionMode == 'diffraction':
			self.logger.info('Inserting beam stop')
			t4 = threading.Thread(target=self.insertBeamstop())
		else:
			t4 = threading.Thread(target=self.dummy())

		while t1.isAlive() or t2.isAlive() or t3.isAlive() or t4.isAlive():
			time.sleep(0.5)
		## make sure shutter override is activated
		try:
			self.instrument.tem.ShutterControl = True
		except:
			# maybe tem has no such function
			pass

	def doAfterAcquire(self):
		'''
		Things to do after acquiring the image. Overwritable by subclasses
		such as MoveAcquisition to skip the real action.
		'''
		try:
			self._doAfterAcquire()
		except RuntimeError as e:
			# instrument emit RuntimeError through proxy
			self.logger.error(e)

	def _doAfterAcquire(self):
		'''
		Things to do after each image acquisition.  This can slow things
		down. Since it will try to do it every time.
		'''
		if self.instrument.tem.ProjectionMode == 'diffraction':
			self.logger.info('Retracting beam stop')
			self.removeBeamstop()

	def insertBeamstop(self):
		self.instrument.tem.BeamstopPosition = 'in'

	def removeBeamstop(self):
		self.instrument.tem.BeamstopPosition = 'out'

	def isFakeImageArray(self, imagearray):
		'''
		Fake image transfer from camera to reduce transfer time.
		General only gives 8x8 image with the mean and standard
		deviation of the real array.
		'''
		if imagearray.shape == (8,8):
			return True
		return False

	def isFakeImageObj(self, imagedata):
		'''
		Same rule as isFakeImageArray but get shape from
		sinedon imagedata object without loading the array
		to get shape and save the read time on large image.
		'''
		shape = imagedata.imageshape()
		if shape == (8,8):
			return True
		return False

	def acquireCameraImageData(self, scopeclass=leginondata.ScopeEMData, allow_retracted=False, type='normal', force_no_frames=False):
		'''Acquire a raw image from the currently configured CCD camera
		Exceptions are caught and return None
		'''
		try:
			imagedata = self.acquireRawCameraImageData(scopeclass=scopeclass, allow_retracted=allow_retracted, type=type, force_no_frames=force_no_frames)
			return imagedata
		except Exception, e:
			self.logger.error(e)
			return None

	def acquireRawCameraImageData(self, scopeclass=leginondata.ScopeEMData, allow_retracted=False, type='normal', force_no_frames=False):
		'''Acquire a raw image from the currently configured CCD camera
			Exceptions are raised
		'''
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

		## acquire image, get new scope/camera params
		#cameradata_before = self.instrument.getData(leginondata.CameraEMData)
		self.startExposureTimer()
		if PARALLEL_IMAGING:
			imagedata['image'] = self.parallelImaging()
		else:
			imagedata['image'] = self.instrument.ccdcamera.Image
		self.doAfterAcquire()
		# get scope data after acquiring image so that scope can be simultaneously
		# controlled. refs #6437
		scopedata = self.instrument.getData(scopeclass)
		try:
			scopedata['intended defocus'] = self.intended_defocus
		except AttributeError:
			scopedata['intended defocus'] = scopedata['defocus']
		imagedata['scope'] = scopedata
		cameradata_after = self.instrument.getData(leginondata.CameraEMData)
		## only using cameradata_after, not cameradata_before
		imagedata['camera'] = cameradata_after

		## duplicating 'use frames' here because we may reuse same
		## CameraEMData for multiple versions of AcquisitionImageData
		imagedata['use frames'] = cameradata_after['use frames']

		## default denoised to False so that we can set that flag if performed.
		imagedata['denoised'] = False

		self.readout_done_event.set()
		if imagedata['image'] is None or imagedata['image'].shape == (0,0):
			# image of wrong shape will still go through. Error raised at normalization
			raise RuntimeError('No valid image returned. Check camera software/hardware')
		# image array still in memory.  This should not take extra time.
		if self.isFakeImageArray(imagedata['image']):
			self.logger.warning('Early return gives back fake images to save time')
		return imagedata

	def parallelImaging(self):
		timage = threading.Thread(target=self.liveImage)
		t0 = time.time()
		timage.start()
		time.sleep(6)
		print 'main start',t0
		self.instrument.setCCDCamera('Ceta')
		array = self.instrument.ccdcamera.Image
		print 'main end',time.time()-t0
		timage.join()
		print 'thread joined', time.time()-t0
		return array

	def liveImage(self):
		try:
			t0 = time.time()
			for i in range(2):
				t0l = time.time()
				print 'live%d start' %i,t0
				self.instrument.setCCDCamera('Ceta2')
				image = self.instrument.ccdcamera.Image
				print i, image.mean()
				print 'live%d end' %i,time.time()-t0
		except:
			print 'Failed live Ceta2 test'

	def requireRecentDarkCurrentReferenceOnBright(self):
		# select camera before calling this function
		if hasattr(self.instrument.ccdcamera, 'requireRecentDarkCurrentReferenceOnBright'):
			return self.instrument.ccdcamera.requireRecentDarkCurrentReferenceOnBright()
		return False

	def updateCameraDarkCurrentReference(self, warning=True):
		if not self.requireRecentDarkCurrentReferenceOnBright():
			if warning:
				self.logger.warning('Camera does not require dark current reference')
			return
		try:
			self.logger.info('Updating hardware dark current reference')
			self.instrument.ccdcamera.updateDarkCurrentReference()
			self.logDarkCurrentReferenceUpdated()
		except:
			raise

	def logDarkCurrentReferenceUpdated(self):
		ccdcameradata = self.instrument.getCCDCameraData()
		q = leginondata.CameraDarkCurrentUpdatedData(hostname=ccdcameradata['hostname'])
		q.insert(force=True)
