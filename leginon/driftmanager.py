#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import watcher
import event, data
import uidata
import camerafuncs
import correlator
import peakfinder
import calibrationclient
import Numeric
import time
import threading
import presets
import copy

class DriftManager(watcher.Watcher):
	eventinputs = watcher.Watcher.eventinputs + [event.DriftDetectedEvent, event.AcquisitionImagePublishEvent, event.NeedTargetShiftEvent]
	eventoutputs = watcher.Watcher.eventoutputs + [event.DriftDoneEvent, event.ImageTargetShiftPublishEvent, event.ChangePresetEvent]
	def __init__(self, id, session, nodelocations, **kwargs):
		watchfor = [event.DriftDetectedEvent, event.AcquisitionImagePublishEvent]
		watcher.Watcher.__init__(self, id, session, nodelocations, watchfor, **kwargs)

		self.correlator = correlator.Correlator()
		self.peakfinder = peakfinder.PeakFinder()
		self.cam = camerafuncs.CameraFuncs(self)
		self.pixsizeclient = calibrationclient.PixelSizeCalibrationClient(self)
		self.presetsclient = presets.PresetsClient(self)
		self.addEventInput(event.NeedTargetShiftEvent, self.handleNeedShift)

		self.references = {}
		self.abortevent = threading.Event()

		self.defineUserInterface()
		self.start()

	def handleNeedShift(self, ev):
		imageid = ev['imageid']
		for key,value in self.references.items():
			imid = value['imageid']
			if imid == imageid:
				im = value['image']
				shift = self.calcShift(im)
				self.references[key]['shift'] = shift
				self.publishImageShifts(requested=True)
				break
		self.confirmEvent(ev)

	def calcShift(self, im):
		## go through preset manager to ensure we follow the right
		## cycle
		pname = im['preset']['name']
		print 'PNAME', pname
		self.presetsclient.toScope(pname)

		## set the original state of the image
		emdata = copy.deepcopy(im['scope'])
		newemdata = self.fixEM(emdata)
		camdata = im['camera']
		self.publishRemote(newemdata)
		self.publishRemote(camdata)

		## acquire new image
		newim = self.acquireImage()

		print 'OLD IMAGE'
		print '  image shift: ', im['scope']['image shift']
		print '  stage position: ', im['scope']['stage position']
		print 'NEW IMAGE'
		print '  image shift: ', newim['scope']['image shift']
		print '  stage position: ', newim['scope']['stage position']

		## do correlation
		self.correlator.insertImage(im['image'])
		self.correlator.insertImage(newim['image'])
		pc = self.correlator.phaseCorrelate()
		peak = self.peakfinder.subpixelPeak(newimage=pc)
		rows,cols = self.peak2shift(peak, pc.shape)
		print 'ROWS/COLS', rows, cols
		return {'rows':rows,'columns':cols}

	def processData(self, newdata):
		if isinstance(newdata, data.AcquisitionImageData):
			self.processImageData(newdata)
		if isinstance(newdata, data.AllEMData):
			self.monitorDrift(newdata)

	def processImageData(self, imagedata):
		'''
		This should update a dictionary of most recent acquisitions
		For now, this is keyed on the node id from where the image
		came.  So we are keeping track of the lastest acquisition
		from each node.
		'''
		nodeid = imagedata['id'][:-1]
		imageid = imagedata['id']
		self.references[nodeid] = {'imageid': imageid, 'image': imagedata, 'shift': {}}

	def uiMonitorDrift(self):
		## calls monitorDrift in a new thread
		t = threading.Thread(target=self.monitorDrift)
		t.setDaemon(1)
		t.start()

	def fixEM(self, emdata):
		emcopy = copy.deepcopy(emdata)
		## only set stage x and y
		for key in emcopy['stage position'].keys():
			if key not in ('x','y'):
				del emcopy['stage position'][key]
		## do not set focus
		try:
			emcopy['focus'] = None
		except:
			pass
		return emcopy

	def monitorDrift(self, emdata=None):
		print 'DriftManager monitoring drift'
		if emdata is not None:
			## use emdata to set up scope and camera
			emdata['id'] = ('all em',)

			newemdata = self.fixEM(emdata)
			self.publishRemote(newemdata)
			mag = newemdata['magnification']
		else:
			## use current state
			magdata = self.researchByDataID(('magnification',))
			mag = magdata['magnification']

		## acquire images, measure drift
		self.abortevent.clear()
		self.acquireLoop(mag)

		## publish ImageTargetShiftData
		self.publishImageShifts(requested=False)

		## DriftDoneEvent
		## only output if this was called from another node
		if emdata is not None:
			ev = event.DriftDoneEvent()
			self.outputEvent(ev)

	def publishImageShifts(self, requested=False):
		print 'PUBLISH IMAGE SHIFTS'
		to_publish = {}
		for value in self.references.values():
			if not requested:
				value['shift'] = {}
			to_publish[value['imageid']] = value['shift']
		print 'TO PUBLISH', to_publish
		dat = data.ImageTargetShiftData(id=self.ID(), shifts=to_publish, requested=requested)
		self.publish(dat, pubevent=True, confirm=True)

	def acquireImage(self):
		imagedata = self.cam.acquireCameraImageData()
		self.im.set(imagedata['image'])
		return imagedata

	def acquireLoop(self, mag):

		## acquire first image
		imagedata = self.acquireImage()
		numdata = imagedata['image']
		t0 = imagedata['scope']['system time']
		self.correlator.insertImage(numdata)
		pixsize = self.pixsizeclient.retrievePixelSize(mag)
		print 'PIXSIZE AT %sx is %s' % (mag, pixsize)

		## ensure that loop executes once
		current_drift = self.threshold.get() + 1.0
		while current_drift > self.threshold.get():
			## wait for interval
			time.sleep(self.pausetime.get())

			## acquire next image
			imagedata = self.acquireImage()
			numdata = imagedata['image']
			binning = imagedata['camera']['binning']['x']
			t1 = imagedata['scope']['system time']
			self.correlator.insertImage(numdata)

			## do correlation
			pc = self.correlator.phaseCorrelate()
			peak = self.peakfinder.subpixelPeak(newimage=pc)
			rows,cols = self.peak2shift(peak, pc.shape)
			dist = Numeric.hypot(rows,cols)
			print 'DRIFT PIXELS', dist

			## calculate drift 
			meters = dist * binning * pixsize
			# rely on system time of EM node
			seconds = t1 - t0
			current_drift = meters / seconds
			print 'DRIFT RATE:  %.4e' % (current_drift,)
			self.driftvalue.set(current_drift)

			## t0 becomes t1 and t1 will be reset for next image
			t0 = t1

			## check for abort
			if self.abortevent.isSet():
				return 'aborted'

		return 'success'

	def abort(self):
		self.abortevent.set()

	def getMag(self):
		magdata = self.researchByDataID(('magnification',))
		mag = magdata['magnification']
		return mag

	def peak2shift(self, peak, shape):
		shift = list(peak)
		half = shape[0] / 2, shape[1] / 2
		if peak[0] > half[0]:
			shift[0] = peak[0] - shape[0]
		if peak[1] > half[1]:
			shift[1] = peak[1] - shape[1]
		return tuple(shift)

	def uiMeasureDrift(self):
		## configure camera
		camconfig = self.cam.cameraConfig()
		camdata = self.cam.configToEMData(camconfig)
		self.cam.currentCameraEMData(camdata)
		mag = self.getMag()
		pixsize = self.pixsizeclient.retrievePixelSize(mag)
		print 'PIXSIZE', pixsize

		## acquire first image
		imagedata = self.acquireImage()
		numdata = imagedata['image']
		t0 = imagedata['scope']['system time']
		self.correlator.insertImage(numdata)

		# pause
		time.sleep(self.pausetime.get())
		
		## acquire next image
		imagedata = self.acquireImage()
		numdata = imagedata['image']
		t1 = imagedata['scope']['system time']
		self.correlator.insertImage(numdata)

		## do correlation
		pc = self.correlator.phaseCorrelate()
		peak = self.peakfinder.subpixelPeak(newimage=pc)
		rows,cols = self.peak2shift(peak, pc.shape)
		dist = Numeric.hypot(rows,cols)
		print 'PIXEL DISTANCE', dist

		## calculate drift 
		meters = dist * pixsize
		print 'METERS', meters
		# rely on system time of EM node
		seconds = t1 - t0
		print 'SECONDS', seconds
		current_drift = meters / seconds
		print 'Drift Rate:  %.4f' % (current_drift,)
		self.driftvalue.set(current_drift)

	def targetsToDatabase(self):
		for target in self.targetlist:
			self.publish(target, database=True)

	def defineUserInterface(self):
		watcher.Watcher.defineUserInterface(self)
		# turn on data queue by default
		self.uidataqueueflag.set(False)

		self.threshold = uidata.Float('Threshold (m)', 2e-10, 'rw', persist=True)
		self.pausetime = uidata.Float('Pause Time (s)', 2.0, 'rw', persist=True)
		abortmeth = uidata.Method('Abort', self.abort)

		camconfig = self.cam.configUIData()
		measuremeth = uidata.Method('Measure Drift Once', self.uiMeasureDrift)
		monitormeth = uidata.Method('Monitor Drift', self.uiMonitorDrift)
		self.driftvalue = uidata.Float('Drift Rate', 0.0, 'r')
		
		self.im = uidata.Image('Drift Image', None, 'r')

		#subcont = uidata.Container('Sub')
		#subcont.addObjects((self.threshold,))

		container = uidata.LargeContainer('Drift Manager')
		container.addObjects((abortmeth, self.threshold,self.pausetime,camconfig, measuremeth, monitormeth, self.driftvalue, self.im))
		self.uiserver.addObject(container)
