import node
import data
import fftengine
import correlator
import peakfinder
import event
import time
import timer
import cameraimage
import camerafuncs
import threading
import calibrationclient
import gonmodel

class GonModeler(node.Node):
	def __init__(self, id, session, nodelocations, **kwargs):
		self.cam = camerafuncs.CameraFuncs(self)
		ffteng = fftengine.fftNumeric()
		#ffteng = fftengine.fftFFTW(planshapes=(), estimate=1)
		self.correlator = correlator.Correlator(ffteng)
		self.peakfinder = peakfinder.PeakFinder()
		self.settle = 2.0
		self.threadstop = threading.Event()
		self.threadlock = threading.Lock()
		self.calclient = calibrationclient.ModeledStageCalibrationClient(self)

		node.Node.__init__(self, id, session, nodelocations, **kwargs)
		self.defineUserInterface()
		self.start()

	# calibrate needs to take a specific value
	def loop(self, axis, points, interval):
		## set camera state
		camconfig = self.cam.config()
		camstate = camconfig['state']
		self.cam.state(camstate)

		mag = self.getMagnification()
		self.writeHeader(mag, axis)

		self.oldimagedata = None
		self.acquireNextPosition(axis)
		currentpos = self.getStagePosition()

		for i in range(points):
			t = timer.Timer('loop')
			if self.threadstop.isSet():
				print 'loop breaking before all points done'
				t.stop()
				break
			currentpos['stage position'][axis] += interval
			datalist = self.acquireNextPosition(axis, currentpos)
			self.writeData(mag, axis, datalist)
			t.stop()
		print 'loop done'
		self.threadlock.release()

	def acquireNextPosition(self, axis, state=None):
		## go to state
		if state is not None:
			newemdata = data.EMData(('scope',), em=state)
			self.publishRemote(newemdata)
			time.sleep(self.settle)

		## acquire image
		newimagedata = self.cam.acquireCameraImageData(correction=0)
		self.publish(newimagedata, pubevent=True)
		newnumimage = newimagedata['image']

		## insert into correlator
		self.correlator.insertImage(newnumimage)

		## cross correlation if oldimagedata exists
		if self.oldimagedata is not None:
			## cross correlation
			crosscorr = self.correlator.phaseCorrelate()
			
			## subtract auto correlation
			crosscorr -= self.autocorr

			## peak finding
			self.peakfinder.setImage(crosscorr)
			self.peakfinder.subpixelPeak()
			peak = self.peakfinder.getResults()
			peakvalue = peak['subpixel peak value']
			shift = correlator.wrap_coord(peak['subpixel peak'], crosscorr.shape)
			binx = newimagedata['camera']['binning']['x']
			biny = newimagedata['camera']['binning']['y']
			pixelsyx = biny * shift[0], binx * shift[1]
			pixelsx = pixelsyx[1]
			pixelsy = pixelsyx[0]
			pixelsh = abs(pixelsx + 1j * pixelsy)

			## calculate stage shift
			avgpos = {}
			pos0 = self.oldimagedata['scope']['stage position'][axis]
			pos1 = newimagedata['scope']['stage position'][axis]
			deltapos = pos1 - pos0
			avgpos[axis] = (pos0 + pos1) / 2.0

			otheraxis = self.otheraxis(axis)
			otherpos0 = self.oldimagedata['scope']['stage position'][otheraxis]
			otherpos1 = newimagedata['scope']['stage position'][otheraxis]
			avgpos[otheraxis] = (otherpos0 + otherpos1) / 2.0

			datalist = [avgpos['x'], avgpos['y'], deltapos, pixelsx, pixelsy]

		else:
			datalist = []

		self.correlator.insertImage(newnumimage)
		self.autocorr = self.correlator.phaseCorrelate()
		self.oldimagedata = newimagedata

		return datalist

	def otheraxis(self, axis):
		if axis == 'x':
			return 'y'
		if axis == 'y':
			return 'x'

	def writeHeader(self, mag, axis):
		'''
		header:
			magnification
			axis
		'''
		padmagstr = '%06d' % (int(mag),)
		magstr = str(int(mag))
		filename = padmagstr + axis + '.data'
		f = open(filename, 'a')
		f.write(magstr + '\n')
		f.write(axis + '\n')
		f.close()

	def writeData(self, mag, axis, datalist):
		padmagstr = '%06d' % (int(mag),)
		magstr = str(int(mag))
		filename = padmagstr + axis + '.data'
		strdatalist = []
		for item in datalist:
			strdatalist.append(str(item))
		f = open(filename, 'a')
		datastr = '\t'.join(strdatalist)
		f.write(datastr + '\n')
		f.close()

	def uiFit(self, datfile, terms):
		self.fit(datfile, terms, magonly=0)
		return ''

	def uiMagOnly(self, datfile, terms):
		self.fit(datfile, terms, magonly=1)
		return ''

	def fit(self, datfile, terms, magonly=1):
		magfile = None
		# modfile  -> moddict
		# magfile => magdict
		dat = gonmodel.GonData(datfile)
		axis = dat.axis
		mag = dat.mag

		mod = gonmodel.GonModel()
		mod.fit_data(dat, terms)

		mod_dict = mod.toDict()
		mag_dict = dat.dict()

		self.calclient.setMagCalibration(mag, mag_dict)
		if magonly:
			return
		self.calclient.setModel(axis, mod_dict)

	def getStagePosition(self):
		dat = self.researchByDataID(('stage position',))
		return dat['em']

	def getMagnification(self):
		dat = self.researchByDataID(('magnification',))
		return dat['em']['magnification']

	def defineUserInterface(self):
		nodespec = node.Node.defineUserInterface(self)

		axes = self.registerUIData('axes', 'array', default=('x','y'))
		argspec = (
			self.registerUIData('Axis', 'string', default='x', choices=axes),
			self.registerUIData('Points', 'integer', default=200),
			self.registerUIData('Interval', 'float', default=5e-6),
			)
		start = self.registerUIMethod(self.uiStartLoop, 'Start', argspec)
		stop = self.registerUIMethod(self.uiStopLoop, 'Stop', ())
		measure = self.registerUIContainer('Measure', (start, stop))
		argspec = (
			self.registerUIData('Data File', 'string'),
			self.registerUIData('Terms', 'integer')
		)
		fit = self.registerUIMethod(self.uiFit, 'Fit Model', argspec)
		magonly = self.registerUIMethod(self.uiMagOnly, 'Mag Only', argspec)

		modelcont = self.registerUIContainer('Model', (measure,fit,magonly))

		camconfig = self.cam.configUIData()

		self.registerUISpec('Goniometer Modeler', (modelcont, camconfig, nodespec))

	def uiStartLoop(self, axis, points, interval):
		if not self.threadlock.acquire(0):
			return ''
		self.threadstop.clear()
		t = threading.Thread(target=self.loop, args=(axis, points, interval))
		t.setDaemon(1)
		t.start()
		return ''

	def uiStopLoop(self):
		self.threadstop.set()
		return ''
