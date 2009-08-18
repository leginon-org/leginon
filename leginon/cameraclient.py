import leginondata
import threading

class CameraClient(object):
	def __init__(self):
		self.resetRepeatConfig()
		self.exposure_start_event = threading.Event()
		self.exposure_done_event = threading.Event()
		self.readout_done_event = threading.Event()

	def clearCameraEvents(self):
		self.exposure_start_event.clear()
		self.exposure_done_event.clear()
		self.readout_done_event.clear()

	def waitExposureDone(self):
		self.exposure_done_event.wait()

	def waitReadoutDone(self):
		self.readout_done_event.wait()

	def startExposureTimer(self):
		'''
		We want to approximate when the CCD exposure is done,
		but not wait for the readout, which can take a lot longer.
		This will set a timer that will generate an event when
		we think the exposure should be done.
		'''
		extratime = 1.0
		print 'Extra time for exposure: %s (tune this lower to save time)' % (extratime,)
		exposure_seconds = self.instrument.ccdcamera.ExposureTime / 1000.0
		waittime = exposure_seconds + extratime
		t = threading.Timer(waittime, self.exposure_done_event.set)
		self.exposure_start_event.set()
		t.start()

	def resetRepeatConfig(self):
		self.repeat_scopedata = None
		self.repeat_cameradata = None

	def acquireCameraImageData(self, repeatconfig=False, scopeclass=leginondata.ScopeEMData, allow_retracted=False):
		'''Acquire a raw image from the currently configured CCD camera'''
		if not allow_retracted:
			try:
				inserted = self.instrument.ccdcamera.Inserted
			except:
				inserted = True
			if not inserted:
				self.logger.info('inserting camera')
				self.instrument.ccdcamera.Inserted = True

		imagedata = leginondata.CameraImageData()
		imagedata['session'] = self.session
		if repeatconfig and None not in (self.repeat_scopedata, self.repeat_cameradata):
			## acquire image, use previous scope/camera params, except system time
			imagedata['scope'] = self.repeat_scopedata
			imagedata['camera'] = self.repeat_cameradata
			for key in ('scope','camera'):
				if 'system time' in imagedata[key]:
					imagedata[key]['system time'] = self.instrument.tem.SystemTime
		else:
			## acquire image, get new scope/camera params
			scopedata = self.instrument.getData(scopeclass)
			cameradata = self.instrument.getData(leginondata.CameraEMData)
			imagedata['scope'] = scopedata
			imagedata['camera'] = cameradata
			self.repeat_scopedata = imagedata['scope']
			self.repeat_cameradata = imagedata['camera']
		self.startExposureTimer()
		imagedata['image'] = self.instrument.ccdcamera.Image
		self.readout_done_event.set()
		return imagedata
