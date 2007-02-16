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
import acquisition
import rctacquisition

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
	eventinputs = watcher.Watcher.eventinputs + [event.DriftMonitorRequestEvent, event.NeedTargetShiftEvent, event.PresetChangedEvent]
	eventoutputs = watcher.Watcher.eventoutputs + [event.DriftMonitorResultEvent, event.ChangePresetEvent, event.PresetLockEvent, event.PresetUnlockEvent, event.AcquisitionImageDriftPublishEvent]
	def __init__(self, id, session, managerlocation, **kwargs):
		watchfor = [event.DriftMonitorRequestEvent]
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

		### Some parameters of the original acquisition were not set by
		### the presets manager, so we need to override them here using
		### info from the original image.  Also, the preset may have
		### changed since the original image was acquired.  The drift
		### manager can be used to adjust targets after a preset is
		### modified, so it is good to use many of the new preset's
		### parameters.  However, some of the new parameters will
		### break the drift manager.  If the old preset camera config is
		### different than the new one, then correlations will fail.

		# Use camera config of original image to make sure correlation works
		oldcam = im['camera']
		newcam = data.CameraEMData()
		newcam['dimension'] = oldcam['dimension']
		newcam['binning'] = oldcam['binning']
		newcam['offset'] = oldcam['offset']
		newcam['exposure time'] = oldcam['exposure time']
		self.instrument.setData(newcam)

		# other things that make correlation difficult if they changed:
		# stage tilt also ???
		# what if preset mag changed ???

		## acquire new image using different correction channel
		chan = im['correction channel']
		if chan in (None, 0):
			newchan = 1
		else:
			newchan = 0
		newcamim = self.acquireImage(channel=newchan)

		## store new version of image to database
		newim = self.newImageVersion(im, newcamim)

		## do correlation
		self.correlator.insertImage(im['image'])
		self.correlator.insertImage(newim['image'])
		pc = self.correlator.phaseCorrelate()
		peak = self.peakfinder.subpixelPeak(newimage=pc)
		rows,cols = self.peak2shift(peak, pc.shape)

		self.setImage(pc, 'Correlation')
		self.setTargets([(peak[1],peak[0])], 'Peak')

		self.logger.info('rows %s, columns %s' % (rows, cols))
		## publish AcquisitionImageDriftData here
		imagedrift = data.AcquisitionImageDriftData()
		imagedrift['session'] = self.session
		imagedrift['old image'] = im
		imagedrift['new image'] = newim
		imagedrift['rows'] = rows
		imagedrift['columns'] = cols
		imagedrift['system time'] = newim['scope']['system time']
		self.publish(imagedrift, database=True, dbforce=True, pubevent=True)

		self.setStatus('idle')
		self.confirmEvent(ev)

	## much of the following method was stolen from acquisition.py
	def newImageVersion(self, oldimagedata, newimagedata):
		## store EMData to DB to prevent referencing errors
		self.publish(newimagedata['scope'], database=True)
		self.publish(newimagedata['camera'], database=True)

		## convert CameraImageData to AcquisitionImageData
		newimagedata = data.AcquisitionImageData(initializer=newimagedata)
		## then add stuff from old imagedata
		newimagedata['preset'] = oldimagedata['preset']
		newimagedata['label'] = oldimagedata['label']
		newimagedata['target'] = oldimagedata['target']
		newimagedata['list'] = oldimagedata['list']
		newimagedata['emtarget'] = oldimagedata['emtarget']
		newimagedata['version'] = oldimagedata['version'] + 1
		target = newimagedata['target']
		if target is not None and 'grid' in target and target['grid'] is not None:
			newimagedata['grid'] = target['grid']

		## set the 'filename' value
		if newimagedata['label'] == 'RCT':
			rctacquisition.setImageFilename(newimagedata)
		else:
			acquisition.setImageFilename(newimagedata)

		self.logger.info('Publishing new version of image...')
		self.publish(newimagedata, database=True, dbforce=True)
		return newimagedata

	def uiDeclareDrift(self):
		self.declareDrift('manual')

	def processData(self, newdata):
		self.logger.info('processData')
		if isinstance(newdata, data.DriftMonitorRequestData):
			self.logger.info('DriftMonitorRequest')
			self.startTimer('monitorDrift')
			self.monitorDrift(newdata)
			self.stopTimer('monitorDrift')

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
		status,final = self.acquireLoop(target, threshold=threshold)
		if status == 'drifted':
			## declare drift above threshold
			self.declareDrift('threshold')

		## Generate DriftMonitorResultData
		## only output if this was called from another node
		if driftdata is not None:
			self.logger.info('Publishing DriftMonitorResultData...')
			result = data.DriftMonitorResultData()
			result['status'] = status
			result['final'] = final
			self.publish(result, pubevent=True, database=True, dbforce=True)
		self.logger.info('DriftManager done monitoring drift')
		self.setStatus('idle')

	def acquireImage(self, channel=0):
		self.startTimer('drift acquire')
		self.instrument.setCorrectionChannel(channel)
		imagedata = self.instrument.getData(data.CorrectedCameraImageData)
		if imagedata is not None:
			self.setImage(imagedata['image'], 'Image')
		self.stopTimer('drift acquire')
		return imagedata

	def acquireLoop(self, target=None, threshold=None):
		## acquire first image
		corchan = 0
		imagedata = self.acquireImage(channel=corchan)
		if imagedata is None:
			return 'aborted', None
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

		status = 'ok'
		while 1:
			## wait for interval
			self.startTimer('drift pause')
			time.sleep(self.settings['pause time'])
			self.stopTimer('drift pause')

			## acquire next image at different correction channel than previous
			if corchan:
				corchan = 0
			else:
				corchan = 1
			imagedata = self.acquireImage(channel=corchan)
			numdata = imagedata['image']
			binning = imagedata['camera']['binning']['x']
			t1 = imagedata['scope']['system time']
			self.correlator.insertImage(numdata)

			## do correlation
			self.startTimer('drift correlate')
			pc = self.correlator.phaseCorrelate()
			self.stopTimer('drift correlate')
			self.startTimer('drift peak')
			peak = self.peakfinder.subpixelPeak(newimage=pc)
			self.stopTimer('drift peak')
			rows,cols = self.peak2shift(peak, pc.shape)
			dist = Numeric.hypot(rows,cols)

			self.setImage(pc, 'Correlation')
			self.setTargets([(peak[1],peak[0])], 'Peak')

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

			if current_drift < threshold:
				return status, d
			else:
				status = 'drifted'

			## check for abort
			if self.abortevent.isSet():
				return 'aborted', d

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
		imagedata = self.acquireImage(0)
		numdata = imagedata['image']
		t0 = imagedata['scope']['system time']
		self.correlator.insertImage(numdata)

		# pause
		time.sleep(self.settings['pause time'])
		
		## acquire next image
		imagedata = self.acquireImage(1)
		numdata = imagedata['image']
		t1 = imagedata['scope']['system time']
		self.correlator.insertImage(numdata)

		## do correlation
		pc = self.correlator.phaseCorrelate()
		peak = self.peakfinder.subpixelPeak(newimage=pc)
		rows,cols = self.peak2shift(peak, pc.shape)
		dist = Numeric.hypot(rows,cols)

		self.setImage(pc, 'Correlation')
		self.setTargets([(peak[1],peak[0])], 'Peak')

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

