#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
import node
import data
import correlator
import peakfinder
import event
import time
import timer
import camerafuncs
import threading
import calibrationclient
import gonmodel
import uidata
import string
import math
import EM
import Numeric

class GonModeler(node.Node):
	eventinputs = node.Node.eventinputs + EM.EMClient.eventinputs
	eventoutputs = node.Node.eventoutputs + EM.EMClient.eventoutputs
	def __init__(self, id, session, managerlocation, **kwargs):
		self.correlator = correlator.Correlator()
		self.peakfinder = peakfinder.PeakFinder()
		self.settle = 5.0
		self.threadstop = threading.Event()
		self.threadlock = threading.Lock()
		node.Node.__init__(self, id, session, managerlocation, **kwargs)
		self.emclient = EM.EMClient(self)
		self.cam = camerafuncs.CameraFuncs(self)
		self.calclient = calibrationclient.ModeledStageCalibrationClient(self)
		self.pcal = calibrationclient.PixelSizeCalibrationClient(self)
		self.defineUserInterface()
		self.start()

	# calibrate needs to take a specific value
	def loop(self, label, axis, points, interval):
		## set camera state
		self.cam.uiApplyAsNeeded()

		mag = self.getMagnification()
		ht = self.getHighTension()
		known_pixelsize = self.pcal.retrievePixelSize(mag)

		self.oldimagedata = None
		self.acquireNextPosition(axis)
		currentpos = self.emclient.getScope()['stage position']

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

			measuredpixsize = delta / math.hypot(imx,imy)
			self.logger.info('Measured pixel size %s' % (measuredpixsize,))
			error = abs(measuredpixsize - known_pixelsize) / known_pixelsize
			self.logger.info('Error %s' % (error,))
			if error > self.tolerance.get():
				self.logger.info('Rejected...')
			else:
				self.logger.info('Saving to database...')
				self.writeData(label, ht, mag, axis, gonx, gony, delta, imx, imy)
			t.stop()
		self.logger.info('Loop done')
		self.threadlock.release()

	def acquireNextPosition(self, axis, state=None):
		## go to state
		if state is not None:
			newemdata = data.ScopeEMData()
			newemdata['stage position'] = {axis: state[axis]}
			debugdict = newemdata.toDict(noNone=True)
			self.logger.debug('setScope: ' + str(debugdict))
			self.emclient.setScope(newemdata)
			time.sleep(self.settle)

		## acquire image
		newimagedata = self.cam.acquireCameraImageData(correction=0)
		newnumimage = newimagedata['image']
		self.ui_image.set(newnumimage.astype(Numeric.Float32))

		## insert into correlator
		self.correlator.insertImage(newnumimage)

		## cross correlation if oldimagedata exists
		if self.oldimagedata is not None:
			## cross correlation
			crosscorr = self.correlator.phaseCorrelate()
			
			## subtract auto correlation
			#crosscorr -= self.autocorr

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
		stagedata = data.StageMeasurementData()
		stagedata['label'] = label
		stagedata['magnification'] = mag
		stagedata['axis'] = axis
		stagedata['high tension'] = ht
		stagedata['x'] = gonx
		stagedata['y'] = gony
		stagedata['delta'] = delta
		stagedata['imagex'] = imx
		stagedata['imagey'] = imy
		self.publish(stagedata, database=True, dbforce=True)

	def uiFit(self):
		# label, mag, axis, terms,...
		self.calclient.fit(self.uifitlabel.get(), self.uifitmag.get(), self.uifitaxis.getSelectedValue(), self.uiterms.get(), magonly=0)
		return ''

	def uiMagOnly(self):
		self.calclient.fit(self.uifitlabel.get(), self.uifitmag.get(), self.uifitaxis.getSelectedValue(), self.uiterms.get(), magonly=1)
		return ''

	def getMagnification(self):
		dat = self.emclient.getScope()
		return dat['magnification']

	def getHighTension(self):
		dat = self.emclient.getScope()
		return dat['high tension']

	def defineUserInterface(self):
		nodespec = node.Node.defineUserInterface(self)

		self.ui_image = uidata.Image('GonModeler Image', None, 'rw')

		self.uidatalabel = uidata.String('Label', '', 'rw', persist=True)
		self.uiaxis = uidata.SingleSelectFromList('Axis',  ['x','y'], 0)
		self.uipoints = uidata.Integer('Points', 200, 'rw', persist=True)
		self.uiinterval = uidata.Float('Interval', 5e-6, 'rw', persist=True)
		self.tolerance = uidata.Float('Tolerance (fraction of known pixel size)', 0.25, 'rw', persist=True)
		start = uidata.Method('Start', self.uiStartLoop)
		stop = uidata.Method('Stop', self.uiStopLoop)
		measurecont = uidata.Container('Measure')
		measurecont.addObjects((self.uiaxis, self.uipoints, self.uiinterval, self.uidatalabel, self.tolerance, start, stop))

		self.uifitlabel = uidata.String('Label', '', 'rw', persist=True)
		self.uifitmag = uidata.Integer('Magnification', None, 'rw', persist=True)
		self.uifitaxis = uidata.SingleSelectFromList('Axis',  ['x','y'], 0, persist=True)
		self.uiterms = uidata.Integer('Terms', 5, 'rw', persist=True)
		fit = uidata.Method('Fit Model', self.uiFit)
		magonly = uidata.Method('Mag Only', self.uiMagOnly)

		modelcont = uidata.Container('Model')
		modelcont.addObjects((self.uifitlabel, self.uifitmag, self.uifitaxis, self.uiterms, fit, magonly))

		camconfig = self.cam.uiSetupContainer()

		maincont = uidata.LargeContainer('GonModeler')
		maincont.addObject(measurecont, position={'position':(0,0)})
		maincont.addObject(modelcont, position={'position':(1,0)})
		maincont.addObject(camconfig, position={'position':(2,0)})
		maincont.addObject(self.ui_image, position={'position':(0,1), 'span': (3,1)})

		self.uicontainer.addObject(maincont)

	def uiStartLoop(self):
		if not self.threadlock.acquire(0):
			return ''
		label = self.uidatalabel.get()
		axis = self.uiaxis.getSelectedValue()
		points = self.uipoints.get()
		interval = self.uiinterval.get()
		self.threadstop.clear()
		t = threading.Thread(target=self.loop, args=(label, axis, points, interval))
		t.setDaemon(1)
		t.start()
		return ''

	def uiStopLoop(self):
		self.threadstop.set()
		return ''
