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
try:
	import numarray as Numeric
except:
	import Numeric
import time
import threading
import presets
import copy
import EM
import gui.wx.DriftManager

class DriftManager(watcher.Watcher):
	panelclass = gui.wx.DriftManager.Panel
	settingsclass = data.DriftManagerSettingsData
	defaultsettings = {
		'threshold': 2e-10,
		'pause time': 2.5,
		'camera settings':
			data.CameraSettingsData(
				initializer={
					'dimension': {
						'x': 1024,
						'y': 1024,
					},
					'offset': {
						'x': 0,
						'y': 0,
					},
					'binning': {
						'x': 1,
						'y': 1,
					},
					'exposure time': 1000.0,
				}
			),
	}
	eventinputs = watcher.Watcher.eventinputs + [event.DriftDetectedEvent, event.DriftDeclaredEvent, event.NeedTargetShiftEvent, event.DriftWatchEvent] + EM.EMClient.eventinputs
	eventoutputs = watcher.Watcher.eventoutputs + [event.DriftDoneEvent, event.ImageTargetShiftPublishEvent, event.ChangePresetEvent] + EM.EMClient.eventoutputs
	def __init__(self, id, session, managerlocation, **kwargs):
		watchfor = [event.DriftDetectedEvent]
		watcher.Watcher.__init__(self, id, session, managerlocation, watchfor, **kwargs)
		## the future:
		##  DriftManager is Acquisition node,  it handles two types
		## of events:  DriftWatch and DriftDetected
		## remove watchfor and watcher stuff,
		## then add:
		#acquisition.Acquisition.__init__(self, id, sesison, managerlocation, target_types=('focus',), **kwargs)
		self.addEventInput(event.DriftWatchEvent, self.handleDriftWatchEvent)
		self.addEventInput(event.DriftDeclaredEvent, self.handleDriftDeclaredEvent)

		self.correlator = correlator.Correlator()
		self.peakfinder = peakfinder.PeakFinder()
		self.emclient = EM.EMClient(self)
		self.cam = camerafuncs.CameraFuncs(self)
		self.pixsizeclient = calibrationclient.PixelSizeCalibrationClient(self)
		self.presetsclient = presets.PresetsClient(self)
		self.addEventInput(event.NeedTargetShiftEvent, self.handleNeedShift)

		self.references = {}
		self.abortevent = threading.Event()

		self.start()

	def handleNeedShift(self, ev):
		imageid = ev['imageid']
		for key,value in self.references.items():
			imid = value['imageid']
			if imid == imageid:
				im = value['image']
				emtarget = value['emtarget']
				preset = value['preset']
				shift = self.calcShift(im, preset, emtarget)
				self.references[key]['shift'] = shift
				self.publishImageShifts(requested=True)
				break
		self.confirmEvent(ev)

	def calcShift(self, im, preset, emtarget):
		## go through preset manager to ensure we follow the right
		## cycle
		self.logger.info('Preset name %s' % preset)
		self.presetsclient.toScope(preset, emtarget)

		## acquire new image
		newim = self.acquireImage()

		self.logger.info('Old image, image shift %s, stage position %s'
									% (im['scope']['image shift'], im['scope']['stage position']))
		self.logger.info('New image, image shift %s, stage position %s'
						% (newim['scope']['image shift'], newim['scope']['stage position']))

		## do correlation
		self.correlator.insertImage(im['image'])
		self.correlator.insertImage(newim['image'])
		pc = self.correlator.phaseCorrelate()
		peak = self.peakfinder.subpixelPeak(newimage=pc)
		rows,cols = self.peak2shift(peak, pc.shape)
		self.logger.info('rows %s, columns %s' % (rows, cols))
		return {'rows':rows,'columns':cols}

	def declareDrift(self):
		self.handleDriftDeclaredEvent(evt=None)

	def handleDriftDeclaredEvent(self, evt=None):
		self.logger.info('drift was declared, publishing image shifts...')
		self.publishImageShifts(requested=False)
		if evt is not None:
			self.confirmEvent(evt)

	def processData(self, newdata):
		self.logger.debug('processData')
		if isinstance(newdata, data.DriftDetectedData):
			self.logger.debug('DriftDetectedData')
			self.monitorDrift(newdata)

	def handleDriftWatchEvent(self, driftwatchevent):
		'''
		This should update a dictionary of most recent acquisitions
		For now, this is keyed on the node id from where the image
		came.  So we are keeping track of the lastest acquisition
		from each node.
		'''
		imagedata = driftwatchevent['image']
		label = imagedata['label']
		imageid = imagedata.dbid
		self.logger.debug('handling drift watch event for image %s' % (imageid,))
		self.references[label] = {'imageid': imageid, 'image': imagedata, 'shift': {}, 'emtarget': driftwatchevent['presettarget']['emtarget'], 'preset': driftwatchevent['presettarget']['preset']}

	def uiMonitorDrift(self):
		self.cam.setCameraDict(self.settings['camera settings'].toDict())
		## calls monitorDrift in a new thread
		t = threading.Thread(target=self.monitorDrift)
		t.setDaemon(1)
		t.start()

	def monitorDrift(self, driftdata=None):
		self.logger.info('DriftManager monitoring drift...')
		if driftdata is not None:
			## use driftdata to set up scope and camera
			pname = driftdata['preset']
			emtarget = driftdata['emtarget']
			target = emtarget['target']
			self.presetsclient.toScope(pname, emtarget)
		else:
			target = None

		## acquire images, measure drift
		self.abortevent.clear()
		self.acquireLoop(target)

		## publish ImageTargetShiftData
		self.logger.info('DriftManager publishing image shifts...')
		self.publishImageShifts(requested=False)

		## DriftDoneEvent
		## only output if this was called from another node
		if driftdata is not None:
			self.logger.info('DriftManager sending DriftDoneEvent...')
			ev = event.DriftDoneEvent()
			self.outputEvent(ev)
		self.logger.info('DriftManager done monitoring drift')

	def publishImageShifts(self, requested=False):
		if requested:
			self.logger.info('Publishing requested image shifts...')
		else:
			self.logger.info('Publishing image shifts...')
		to_publish = {}
		for value in self.references.values():
			if not requested:
				value['shift'] = {}
			to_publish[value['imageid']] = value['shift']
		self.logger.info('to publish %s' % to_publish)
		dat = data.ImageTargetShiftData(shifts=to_publish,
																		requested=requested)
		self.publish(dat, pubevent=True)

	def acquireImage(self):
		imagedata = self.cam.acquireCameraImageData()
		if imagedata is not None:
			self.setImage(imagedata['image'])
		return imagedata

	def acquireLoop(self, target=None):

		## acquire first image
		imagedata = self.acquireImage()
		if imagedata is None:
			return 'aborted'
		numdata = imagedata['image']
		t0 = imagedata['scope']['system time']
		self.correlator.insertImage(numdata)
		mag = imagedata['scope']['magnification']
		pixsize = self.pixsizeclient.retrievePixelSize(mag)
		self.logger.info('Pixel size at %sx is %s' % (mag, pixsize))

		## ensure that loop executes once
		threshold = self.settings['threshold']
		current_drift = threshold + 1.0
		while current_drift > threshold:
			## wait for interval
			time.sleep(self.settings['pause time'])

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
			self.logger.info('Pixels drifted %s' % dist)

			## calculate drift 
			meters = dist * binning * pixsize
			rowmeters = rows * binning * pixsize
			colmeters = cols * binning * pixsize
			# rely on system time of EM node
			seconds = t1 - t0
			current_drift = meters / seconds
			self.logger.info('Drift rate: %.4e' % (current_drift,))

			d = data.DriftData(session=self.session, rows=rows, cols=cols, interval=seconds, rowmeters=rowmeters, colmeters=colmeters, target=target)
			self.publish(d, database=True, dbforce=True)

			## t0 becomes t1 and t1 will be reset for next image
			t0 = t1

			## check for abort
			if self.abortevent.isSet():
				return 'aborted'

		return 'success'

	def abort(self):
		self.abortevent.set()

	def getMag(self):
		mag = self.emclient.getScope()['magnification']
		return mag

	def peak2shift(self, peak, shape):
		shift = list(peak)
		half = shape[0] / 2, shape[1] / 2
		if peak[0] > half[0]:
			shift[0] = peak[0] - shape[0]
		if peak[1] > half[1]:
			shift[1] = peak[1] - shape[1]
		return tuple(shift)

	def measureDrift(self):
		## configure camera
		self.cam.setCameraDict(self.settings['camera settings'].toDict())
		mag = self.getMag()
		pixsize = self.pixsizeclient.retrievePixelSize(mag)
		self.logger.info('Pixel size %s' % (pixsize,))

		## acquire first image
		imagedata = self.acquireImage()
		numdata = imagedata['image']
		t0 = imagedata['scope']['system time']
		self.correlator.insertImage(numdata)

		# pause
		time.sleep(self.settings['pause time'])
		
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

		## calculate drift 
		meters = dist * pixsize
		self.logger.info('Pixel distance %s, (%s meters)' % (dist, meters))
		# rely on system time of EM node
		seconds = t1 - t0
		self.logger.info('Seconds %s' % seconds)
		current_drift = meters / seconds
		self.logger.info('Drift rate: %.4f' % (current_drift,))

	def targetsToDatabase(self):
		for target in self.targetlist:
			self.publish(target, database=True)

