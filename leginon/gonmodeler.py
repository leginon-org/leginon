#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
import node
import leginondata
from pyami import correlator, peakfinder
import event
import time
import timer
import threading
import calibrationclient
import gonmodel
import string
import math
import calibrator
import gui.wx.GonModeler

class GonModeler(calibrator.Calibrator):
	panelclass = gui.wx.GonModeler.Panel
	settingsclass = leginondata.GonModelerSettingsData
	defaultsettings = calibrator.Calibrator.defaultsettings
	defaultsettings.update({
		'measure axis': 'x',
		'measure points': 200,
		'measure interval': 5e-6,
		'measure tolerance': 25.0,
		'measure label': '',
		'model axis': 'x',
		'model magnification': None,
		'model terms': 5,
		'model mag only': False,
		'model label': '',
		'model tolerance': 25.0,
	})
	def __init__(self, id, session, managerlocation, **kwargs):
		self.correlator = correlator.Correlator()
		self.peakfinder = peakfinder.PeakFinder()
		self.settle = 5.0
		self.threadstop = threading.Event()
		self.threadlock = threading.Lock()
		calibrator.Calibrator.__init__(self, id, session, managerlocation, **kwargs)
		self.calclient = calibrationclient.ModeledStageCalibrationClient(self)
		self.pcal = calibrationclient.PixelSizeCalibrationClient(self)
		self.corchannel = None

		self.axes = ['x', 'y']

		self.start()

	# calibrate needs to take a specific value
	def loop(self, label, axis, points, interval):
		try:
			if self.initInstruments():
				self.panel.measurementDone()
				return
		except Exception, e:
			self.logger.error('Modeled stage measurement failed: %s' % e)
			self.panel.measurementDone()
			return

		mag, mags = self.getMagnification()
		ht = self.getHighTension()
		if None in [mag, mags, ht]:
			e = 'unable to access instrument'
			self.logger.error('Modeled stage measurement failed: %s' % e)
			self.panel.measurementDone()
			return
		known_pixelsize = self.pcal.retrievePixelSize(None, None, mag)

		self.oldimagedata = None
		self.acquireNextPosition(axis)
		currentpos = self.instrument.tem.StagePosition

		for i in range(points):
			self.logger.info('Acquiring Point %s...' % (i,))
			t = timer.Timer('loop')
			if self.threadstop.isSet():
				self.logger.info('Loop breaking before all points done')
				t.stop()
				break
			currentpos[axis] += interval
			datalist = self.acquireNextPosition(axis, currentpos)
			gonx = datalist[0]
			gony = datalist[1]
			delta = datalist[2]
			imx = datalist[3]
			imy = datalist[4]

			self.logger.info('Position %s, %s' % (gonx, gony))
			self.logger.info('Delta %s' % (delta,))
			self.logger.info('Correlation shift %s, %s' % (imx, imy))

			measuredpixsize = abs(delta) / math.hypot(imx,imy)
			self.logger.info('Measured pixel size %s' % (measuredpixsize,))
			error = abs(measuredpixsize - known_pixelsize) / known_pixelsize
			self.logger.info('Error %s' % (error,))
			if error > self.settings['measure tolerance']/100.0:
				self.logger.info('Rejected...')
			else:
				self.logger.info('Saving to database...')
				self.writeData(label, ht, mag, axis, gonx, gony, delta, imx, imy)
			t.stop()
		self.logger.info('Loop done')
		self.threadlock.release()
		self.panel.measurementDone()
		self.setModelDefaults()

	def acquireNextPosition(self, axis, state=None):
		## go to state
		if state is not None:
			self.instrument.tem.StagePosition = {axis: state[axis]}
			time.sleep(self.settle)

		## alternate correction channel
		if self.corchannel:
			self.corchannel = 0
		else:
			self.corchannel = 1
		self.instrument.setCorrectionChannel(self.corchannel)

		## acquire image
		newimagedata = self.instrument.getData(leginondata.CorrectedCameraImageData)

		newnumimage = newimagedata['image']
		self.setImage(newnumimage, 'Image')

		## insert into correlator
		self.correlator.insertImage(newnumimage)

		## cross correlation if oldimagedata exists
		if self.oldimagedata is not None:
			## cross correlation
			crosscorr = self.correlator.phaseCorrelate()
			self.setImage(crosscorr, 'Correlation')
			
			## subtract auto correlation
			#crosscorr -= self.autocorr

			## peak finding
			self.peakfinder.setImage(crosscorr)
			self.peakfinder.subpixelPeak()
			peakresults = self.peakfinder.getResults()
			peak = peakresults['subpixel peak']
			y,x = peak
			self.setTargets([(x,y)], 'Peak')
			shift = correlator.wrap_coord(peak, crosscorr.shape)
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

		#self.correlator.insertImage(newnumimage)
		#self.autocorr = self.correlator.phaseCorrelate()
		self.oldimagedata = newimagedata

		return datalist

	def otheraxis(self, axis):
		if axis == 'x':
			return 'y'
		if axis == 'y':
			return 'x'

	def writeData(self, label, ht, mag, axis, gonx, gony, delta, imx, imy):
		stagedata = leginondata.StageMeasurementData()
		stagedata['label'] = label
		stagedata['magnification'] = mag
		stagedata['axis'] = axis
		stagedata['high tension'] = ht
		stagedata['x'] = gonx
		stagedata['y'] = gony
		stagedata['delta'] = delta
		stagedata['imagex'] = imx
		stagedata['imagey'] = imy
		stagedata['tem'] = self.instrument.getTEMData()
		stagedata['ccdcamera'] = self.instrument.getCCDCameraData()
		self.publish(stagedata, database=True, dbforce=True)

	def uiFit(self):
		# label, mag, axis, terms,...
		self.initInstruments()
		try:
			if self.settings['model mag only']:
				self.calclient.fitMagOnly(None, None,
													self.settings['model label'],
													self.settings['model magnification'],
													self.settings['model axis'])
			else:
				self.calclient.fit(None, None,
													self.settings['model label'],
													self.settings['model magnification'],
													self.settings['model axis'],
													self.settings['model terms'])
		except Exception, e:
			self.logger.error('Modeled stage fit failed: %s' % e)
		self.panel.calibrationDone()

	def uiStartLoop(self):
		if not self.threadlock.acquire(0):
			self.panel.measurementDone()
			return
		label = self.settings['measure label']
		axis = self.settings['measure axis']
		points = self.settings['measure points']
		interval = self.settings['measure interval']
		self.threadstop.clear()
		self.loop(label, axis, points, interval)
		return

	def uiStopLoop(self):
		self.threadstop.set()
		self.setModelDefaults()
		return

	def setModelDefaults(self):
		print "stopped and changed"
		self.settings['model label'] = self.settings['measure label']
		self.settings['model axis'] = self.settings['measure axis']
		currentmag,allmags = self.getMagnification()
		self.settings['model magnification'] = currentmag
		self.setSettings(self.settings)
