import acquisition
import node, data
import calibrationclient
import camerafuncs

class Drifter(acquisition.Acquisition):
	def __init__(self, id, sesison, nodelocations, **kwargs):
		self.cam = camerafuncs.CameraFuncs(self)

		self.calclient = calibrationclient.CalibrationClient(self)

		acquisition.Acquisition.__init__(self, id, sesison, nodelocations, targetclass=data.TargetData, **kwargs)

	def acquire(self, preset, trial=False):
		'''
		this replaces Acquisition.acquire()
		Instead of acquiring an image, we do autofocus
		'''
		pub = self.publishimages.get()
		drift_timeout = self.drift_timeout.get()
		pause_time = self.pause_time.get()

		### measure drift until timeout

		info1 = self.acquireStateImage(state1, publish_images, settle)
		imagedata1 = info1['imagedata']
		imagecontent1 = imagedata1
		stats1 = info1['image stats']
		actual1 = imagecontent1['scope']
		self.numimage1 = imagecontent1['image']
		self.correlator.insertImage(self.numimage1)

		## for drift check, continue to acquire at state1
		if checkdrift:
			self.sleep(pause_time)

			print 'checking for drift'
			if timeout is None:
				timelimit = None
			else:
				timelimit = time.time() + timeout
			while 1:
				info1 = self.acquireStateImage(state1, publish_images, settle)
				imagedata1 = info1['imagedata']
				imagecontent1 = imagedata1
				stats1 = info1['image stats']
				actual1 = imagecontent1['scope']
				self.numimage1 = imagecontent1['image']
				self.correlator.insertImage(self.numimage1)

				print 'correlation'
				pcimage = self.correlator.phaseCorrelate()

				print 'peak finding'
				self.peakfinder.setImage(pcimage)
				self.peakfinder.subpixelPeak()
				peak = self.peakfinder.getResults()
				peakvalue = peak['subpixel peak value']
				shift = correlator.wrap_coord(peak['subpixel peak'], pcimage.shape)
				drift = abs(shift[0] + 1j * shift[1])
				if drift < 1.0:
					print 'no drift'
					break
				else:
					print 'drift', drift
				
				if timelimit and time.time() > timelimit:
					raise DriftingTimeout()


			data.DriftData(self.ID(), 


	def uiTest(self):
		self.acquire(None)
		return ''

	def defineUserInterface(self):
		acqui = acquisition.Acquisition.defineUserInterface(self)

		self.publishimages = self.registerUIData('Publish Images', 'boolean', default=1, permissions='rw')

		test = self.registerUIMethod(self.uiTest, 'Test Drifter', ())

		prefs = self.registerUIContainer('Drifter Setup', (self.publishimages, test))

		myui = self.registerUISpec('Drifter', (prefs,))
		myui += acqui
		return myui

