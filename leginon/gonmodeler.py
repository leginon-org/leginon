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

class GonModeler(node.Node):
	def __init__(self, id, session, nodelocations, **kwargs):
		self.cam = camerafuncs.CameraFuncs(self)
		self.correlator = correlator.Correlator()
		self.peakfinder = peakfinder.PeakFinder()
		self.settle = 5.0
		self.threadstop = threading.Event()
		self.threadlock = threading.Lock()
		self.calclient = calibrationclient.ModeledStageCalibrationClient(self)

		node.Node.__init__(self, id, session, nodelocations, **kwargs)
		self.defineUserInterface()
		self.start()

	# calibrate needs to take a specific value
	def loop(self, label, axis, points, interval):
		## set camera state
		camconfig = self.cam.cameraConfig()
		emdata = self.cam.configToEMData(camconfig)
		self.cam.currentCameraEMData(camdata=emdata)

		mag = self.getMagnification()
		ht = self.getHighTension()

		self.oldimagedata = None
		self.acquireNextPosition(axis)
		currentpos = self.getStagePosition()
		print 'CURRENT POS', currentpos

		for i in range(points):
			print 'Point %s' % (i,)
			t = timer.Timer('loop')
			if self.threadstop.isSet():
				print 'loop breaking before all points done'
				t.stop()
				break
			currentpos['stage position'][axis] += interval
			datalist = self.acquireNextPosition(axis, currentpos)
			gonx = datalist[0]
			gony = datalist[1]
			delta = datalist[2]
			imx = datalist[3]
			imy = datalist[4]
			self.writeData(label, ht, mag, axis, gonx, gony, delta, imx, imy)
			t.stop()
		print 'loop done'
		self.threadlock.release()

	def acquireNextPosition(self, axis, state=None):
		## go to state
		if state is not None:
			newemdata = data.ScopeEMData(id=('scope',), initializer=state)
			self.publishRemote(newemdata)
			time.sleep(self.settle)

		## acquire image
		newimagedata = self.cam.acquireCameraImageData(correction=0)
		self.publish(newimagedata, pubevent=True, dbforce=True)
		newnumimage = newimagedata['image']
		print 'NEWNUMIMAGE shape', newnumimage.shape

		## insert into correlator
		self.correlator.insertImage(newnumimage)

		print 'INSERTED INTO CORR'
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

	def uiConvert(self):
		self.file2db(self.uiconvertfilename.get(), self.uidatalabel.get())

	def file2db(self, filename, label):
		datafile = open(filename, 'r')
		lines = datafile.readlines()
		datafile.close()
		headlines = lines[:2]
		headlines = map(string.split,headlines)
		mag = float(headlines[0][0])
		axis = headlines[1][0]
		print 'mag', mag
		print 'axis', axis

		datalines = lines[2:]
		print 'inserting into DB'
		count = 0
		for dataline in datalines:
			strvalues = dataline.split('\t')
			if len(strvalues) != 5:
				continue
			gonx,gony,delta,imagex,imagey = map(float, strvalues)
			self.writeData(label, mag, axis, gonx, gony, delta, imagex, imagey)
			count += 1
		print 'inserted %s data points' % (count,)

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
		print 'Writing', stagedata
		self.publish(stagedata, database=True, dbforce=True)

	def uiFit(self):
		# label, mag, axis, terms,...
		self.calclient.fit(self.uifitlabel.get(), self.uifitmag.get(), self.uifitaxis.getSelectedValue(), self.uiterms.get(), magonly=0)
		return ''

	def uiMagOnly(self):
		self.calclient.fit(self.uifitlabel.get(), self.uifitmag.get(), self.uifitaxis.getSelectedValue(), self.uiterms.get(), magonly=1)
		return ''

	def getStagePosition(self):
		dat = self.researchByDataID(('stage position',))
		return dat

	def getMagnification(self):
		dat = self.researchByDataID(('magnification',))
		return dat['magnification']

	def getHighTension(self):
		dat = self.researchByDataID(('high tension',))
		return dat['high tension']

	def defineUserInterface(self):
		nodespec = node.Node.defineUserInterface(self)

		self.uidatalabel = uidata.String('Label', '', 'rw', persist=True)
		self.uiaxis = uidata.SingleSelectFromList('Axis',  ['x','y'], 0)
		self.uipoints = uidata.Integer('Points', 200, 'rw', persist=True)
		self.uiinterval = uidata.Float('Interval', 5e-6, 'rw', persist=True)
		start = uidata.Method('Start', self.uiStartLoop)
		stop = uidata.Method('Stop', self.uiStopLoop)
		self.uiconvertfilename = uidata.String('Data File', '', 'rw')
		convert = uidata.Method('File->DB', self.uiConvert)

		measurecont = uidata.Container('Measure')
		measurecont.addObjects((self.uiaxis, self.uipoints, self.uiinterval, self.uidatalabel, start, stop, self.uiconvertfilename, convert))

		self.uifitlabel = uidata.String('Label', '', 'rw', persist=True)
		self.uifitmag = uidata.Integer('Magnification', None, 'rw', persist=True)
		self.uifitaxis = uidata.SingleSelectFromList('Axis',  ['x','y'], 0, persist=True)
		self.uiterms = uidata.Integer('Terms', 5, 'rw', persist=True)
		fit = uidata.Method('Fit Model', self.uiFit)
		magonly = uidata.Method('Mag Only', self.uiMagOnly)

		modelcont = uidata.Container('Model')
		modelcont.addObjects((self.uifitlabel, self.uifitmag, self.uifitaxis, self.uiterms, fit, magonly))

		camconfig = self.cam.configUIData()

		maincont = uidata.LargeContainer('GonModeler')
		maincont.addObjects((measurecont, modelcont, camconfig))
		self.uiserver.addObject(maincont)

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
