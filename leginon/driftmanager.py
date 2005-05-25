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
import instrument

class DriftManager(watcher.Watcher):
	panelclass = gui.wx.DriftManager.Panel
	settingsclass = data.DriftManagerSettingsData
	defaultsettings = {
		'threshold': 3e-10,
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
	eventinputs = watcher.Watcher.eventinputs + [event.DriftDetectedEvent, event.NeedTargetShiftEvent, event.PresetChangedEvent]
	eventoutputs = watcher.Watcher.eventoutputs + [event.DriftDoneEvent, event.ChangePresetEvent, event.PresetLockEvent, event.PresetUnlockEvent, event.AcquisitionImageDriftPublishEvent]
	def __init__(self, id, session, managerlocation, **kwargs):
		watchfor = [event.DriftDetectedEvent]
		watcher.Watcher.__init__(self, id, session, managerlocation, watchfor, **kwargs)

		self.correlator = correlator.Correlator()
		self.peakfinder = peakfinder.PeakFinder()
		self.instrument = instrument.Proxy(self.objectservice, self.session,
																				self.panel)
		self.pixsizeclient = calibrationclient.PixelSizeCalibrationClient(self)
		self.presetsclient = presets.PresetsClient(self)
		self.addEventInput(event.NeedTargetShiftEvent, self.handleNeedShift)

		self.abortevent = threading.Event()

		self.start()

	def handleNeedShift(self, ev):
		self.setStatus('processing')
		## reaquire the image from which the target originated
		im = ev['image']
		## go through preset manager to ensure we follow the right
		## cycle
		presetname = im['preset']['name']
		emtarget = im['emtarget']
		self.logger.info('Preset name %s' % presetname)
		self.presetsclient.toScope(presetname, emtarget)

		## acquire new image
		newim = self.acquireImage()

		self.logger.debug('Old image, image shift %s, stage position %s'
									% (im['scope']['image shift'], im['scope']['stage position']))
		self.logger.debug('New image, image shift %s, stage position %s'
						% (newim['scope']['image shift'], newim['scope']['stage position']))

		## do correlation
		self.correlator.insertImage(im['image'])
		self.correlator.insertImage(newim['image'])
		pc = self.correlator.phaseCorrelate()
		peak = self.peakfinder.subpixelPeak(newimage=pc)
		rows,cols = self.peak2shift(peak, pc.shape)

		self.logger.info('rows %s, columns %s' % (rows, cols))
		## publish AcquisitionImageDriftData here
		imagedrift = data.AcquisitionImageDriftData()
		imagedrift['image'] = im
		imagedrift['rows'] = rows
		imagedrift['columns'] = cols
		imagedrift['system time'] = newim['scope']['system time']
		self.publish(imagedrift, database=True, dbforce=True, pubevent=True)

		self.setStatus('idle')
		self.confirmEvent(ev)

	def uiDeclareDrift(self):
		self.declareDrift('manual')

	def processData(self, newdata):
		self.logger.debug('processData')
		if isinstance(newdata, data.DriftDetectedData):
			self.logger.debug('DriftDetectedData')
			self.monitorDrift(newdata)

	def uiMonitorDrift(self):
		self.instrument.ccdcamera.Settings = self.settings['camera settings']
		## calls monitorDrift in a new thread
		t = threading.Thread(target=self.monitorDrift)
		t.setDaemon(1)
		t.start()

	def monitorDrift(self, driftdata=None):
		self.setStatus('processing')
		self.logger.info('DriftManager monitoring drift...')
		if driftdata is not None:
			## use driftdata to set up scope and camera
			pname = driftdata['presetname']
			emtarget = driftdata['emtarget']
			threshold = driftdata['threshold']
			target = emtarget['target']
			self.presetsclient.toScope(pname, emtarget)
		else:
			target = None
			threshold = None

		## acquire images, measure drift
		self.abortevent.clear()
		self.acquireLoop(target, threshold=threshold)

		## declare drift above threshold
		declared = data.DriftDeclaredData()
		declared['system time'] = self.instrument.tem.SystemTime
		declared['type'] = 'threshold'
		self.publish(declared, database=True, dbforce=True)

		## DriftDoneEvent
		## only output if this was called from another node
		if driftdata is not None:
			self.logger.info('DriftManager sending DriftDoneEvent...')
			ev = event.DriftDoneEvent()
			self.outputEvent(ev)
		self.logger.info('DriftManager done monitoring drift')
		self.setStatus('idle')

	def acquireImage(self):
		imagedata = self.instrument.getData(data.CorrectedCameraImageData)
		if imagedata is not None:
			self.setImage(imagedata['image'])
		return imagedata

	def acquireLoop(self, target=None, threshold=None):

		## acquire first image
		imagedata = self.acquireImage()
		if imagedata is None:
			return 'aborted'
		numdata = imagedata['image']
		t0 = imagedata['scope']['system time']
		self.correlator.insertImage(numdata)
		mag = imagedata['scope']['magnification']
		tem = imagedata['scope']['tem']
		ccd = imagedata['camera']['ccdcamera']
		pixsize = self.pixsizeclient.retrievePixelSize(tem, ccd, mag)
		self.logger.info('Pixel size at %sx is %s' % (mag, pixsize))

		if threshold is None:
			requested = False
			threshold = self.settings['threshold']
			self.logger.info('using threshold setting: %.2e' % (threshold,))
		else:
			self.logger.info('using requested threshold: %.2e' % (threshold,))
			requested = True
		## ensure that loop executes once
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

			## calculate drift 
			meters = dist * binning * pixsize
			rowmeters = rows * binning * pixsize
			colmeters = cols * binning * pixsize
			# rely on system time of EM node
			seconds = t1 - t0
			current_drift = meters / seconds
			self.logger.info('Drift rate: %.2e' % (current_drift,))

			## publish scope and camera to be used with drift data
			scope = imagedata['scope']
			self.publish(scope, database=True, dbforce=True)
			camera = imagedata['camera']
			self.publish(camera, database=True, dbforce=True)

			d = data.DriftData(session=self.session, rows=rows, cols=cols, interval=seconds, rowmeters=rowmeters, colmeters=colmeters, target=target, scope=scope, camera=camera)
			self.publish(d, database=True, dbforce=True)

			## t0 becomes t1 and t1 will be reset for next image
			t0 = t1

			## check for abort
			if self.abortevent.isSet():
				return 'aborted'

		return 'success'

	def abort(self):
		self.abortevent.set()

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
		self.instrument.ccdcamera.Settings = self.settings['camera settings']
		mag = self.instrument.tem.Magnification
		tem = self.instrument.getTEMData()
		cam = self.instrument.getCCDCameraData()
		pixsize = self.pixsizeclient.retrievePixelSize(tem, cam, mag)
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
		self.logger.info('Pixel distance %s, (%.2e meters)' % (dist, meters))
		# rely on system time of EM node
		seconds = t1 - t0
		self.logger.info('Seconds %s' % seconds)
		current_drift = meters / seconds
		self.logger.info('Drift rate: %.2e' % (current_drift,))

	def targetsToDatabase(self):
		for target in self.targetlist:
			self.publish(target, database=True)

