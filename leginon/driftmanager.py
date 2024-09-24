#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright under
#       Apache License, Version 2.0
#       For terms of the license agreement
#       see  http://leginon.org
#

from leginon import watcher
from leginon import event, leginondata
from pyami import imagefun, correlator, peakfinder
from leginon import calibrationclient
import math
import time
import datetime
import os
import threading
from leginon import presets
import copy
from leginon import EM
import leginon.gui.wx.DriftManager
from leginon import instrument
from leginon import acq as acquisition
from leginon import rctacquisition
from leginon import cameraclient

class DriftManager(watcher.Watcher):
	panelclass = leginon.gui.wx.DriftManager.Panel
	settingsclass = leginondata.DriftManagerSettingsData
	defaultsettings = {
		'threshold': 3e-10,
		'pause time': 2.5,
		'timeout': 30,
		'measure drift interval': 0,
		'camera settings': cameraclient.default_settings,
	}
	eventinputs = watcher.Watcher.eventinputs + [event.DriftMonitorRequestEvent, event.PresetChangedEvent]
	eventoutputs = watcher.Watcher.eventoutputs + [event.DriftMonitorResultEvent, event.ChangePresetEvent, event.PresetLockEvent, event.PresetUnlockEvent, event.AcquisitionImagePublishEvent]
	def __init__(self, id, session, managerlocation, **kwargs):
		watchfor = [event.DriftMonitorRequestEvent]
		watcher.Watcher.__init__(self, id, session, managerlocation, watchfor, **kwargs)

		self.correlator = correlator.Correlator(shrink=True)
		self.peakfinder = peakfinder.PeakFinder()
		self.instrument = instrument.Proxy(self.objectservice, self.session,
																				self.panel)
		self.pixsizeclient = calibrationclient.PixelSizeCalibrationClient(self)
		self.presetsclient = presets.PresetsClient(self)

		self.abortevent = threading.Event()

		self.start()

	def uiDeclareDrift(self):
		self.declareDrift('manual')

	def processData(self, newdata):
		self.logger.info('processData')
		if isinstance(newdata, leginondata.DriftMonitorRequestData):
			self.logger.info('DriftMonitorRequest')
			self.startTimer('monitorDrift')
			self.monitorDrift(newdata)
			self.stopTimer('monitorDrift')

	def uiMeasureDrift(self):
		t = threading.Thread(target=self.measureDrift)
		t.setDaemon(1)
		t.start()

	def uiMonitorDrift(self):
		self.instrument.ccdcamera.Settings = self.settings['camera settings']
		## calls monitorDrift in a new thread
		t = threading.Thread(target=self.monitorDrift)
		t.setDaemon(1)
		t.start()

	def monitorDrift(self, driftdata=None):
		self.setStatus('processing')
		self.logger.info('DriftManager monitoring drift...')
		target = None
		threshold = None
		beamtilt_delta = {'x':0.0,'y':0.0}
		need_tilt = False

		if driftdata is not None:
			## use driftdata to set up scope and camera
			pname = driftdata['presetname']
			emtarget = driftdata['emtarget']
			threshold = driftdata['threshold']
			target = emtarget['target']
			beamtilt_delta = driftdata['beamtilt']
			self.presetsclient.toScope(pname, emtarget)
			presetdata = self.presetsclient.getCurrentPreset()

		# tilt the beam if requested
		need_tilt = beamtilt_delta and (abs(beamtilt_delta['x']) > 1e-6 or abs(beamtilt_delta['y'])) > 1e-6
		if need_tilt:
			bt0 = self.instrument.tem.BeamTilt
			bt1 = {'x':bt0['x']+beamtilt_delta['x'], 'y':bt0['y']+beamtilt_delta['y']}
			self.logger.info('Tilt beam by (x,y)=(%.2f,%.2f) mrad' % (beamtilt_delta['x'],beamtilt_delta['y']))
			self.instrument.tem.BeamTilt = bt1

		## acquire images, measure drift
		self.abortevent.clear()
		# extra pause to wait for image shift to stabilize
		self.logger.info('pausing before loop')
		time.sleep(self.settings['pause time']/2.0)	
		self.logger.info('paused before loop')
		status,final,im = self.acquireLoop(target, threshold=threshold)
		# tilt the beam back if requested
		if need_tilt:
			self.instrument.tem.BeamTilt = bt0
			self.logger.info('Tilt Beam back')

		if status in ('drifted', 'timeout'):
			## declare drift above threshold
			self.declareDrift('threshold')

		if im is None:
			self.logger.error('DriftManager failed monitoring drift')
			self.setStatus('idle')
			return
		## Generate DriftMonitorResultData
		## only output if this was called from another node
		if driftdata is not None:
			self.logger.info('Publishing final drift image...')
			acqim = leginondata.AcquisitionImageData(initializer=im)
			acqim['target'] = target
			acqim['emtarget'] = emtarget
			acqim['preset'] = presetdata
			self.publish(acqim, pubevent=True)

			self.logger.info('Publishing DriftMonitorResultData...')
			result = leginondata.DriftMonitorResultData()
			result['status'] = status
			result['final'] = final
			self.publish(result, pubevent=True, database=True, dbforce=True)
		self.logger.info('DriftManager done monitoring drift')
		self.setStatus('idle')

	def acquireImage(self, channel=0, correct=True):
		self.startTimer('drift acquire')
		imagedata = None
		if correct:
			try:
				imagedata = self.acquireCorrectedCameraImageData(channel, force_no_frames=True)
			except:
				self.logger.warning('Acquiring corrected image failed. Raw image is used')
		if imagedata is None:
			imagedata = self.acquireCameraImageData(force_no_frames=True)
		if imagedata is not None:
			self.setImage(imagedata['image'], 'Image')
		self.stopTimer('drift acquire')
		return imagedata

	def acquireLoop(self, target=None, threshold=None):
		self.logger.info('taking a fake image to remove hysteresis')
		fakeimagedata = self.acquireImage(channel=1)
		self.logger.info('taken the fake image')
		## acquire first image
		# make sure we have waited "pause time" before acquire the first image
		self.logger.info('pausing at loop start')
		time.sleep(self.settings['pause time'])
		self.logger.info('paused at loop start')
		corchan = 0
		imagedata = self.acquireImage(channel=corchan)
		self.logger.info('first image acquired')
		if imagedata is None:
			return 'aborted', None, None
		numdata = imagedata['image']
		t0 = imagedata['scope']['system time']
		self.correlator.insertImage(numdata)
		mag = imagedata['scope']['magnification']
		tem = imagedata['scope']['tem']
		ccd = imagedata['camera']['ccdcamera']
		pixsize = self.pixsizeclient.retrievePixelSize(tem, ccd, mag)

		if threshold is None:
			requested = False
			threshold = self.settings['threshold']
			self.logger.info('using threshold setting: %.2e' % (threshold,))
		else:
			self.logger.info('using requested threshold: %.2e' % (threshold,))
			requested = True

		status = 'ok'
		current_drift = 1.0e-3
		lastdrift1 = 1.0e-3
		lastdrift2 = 1.0e-3
		minutes = self.settings['timeout']
		timeout = time.time() + 60 * minutes
		while 1:
			# make sure we have waited at least "pause time" before acquire
			t1 = self.instrument.tem.SystemTime
			dt = t1 - t0
			pausetime = self.settings['pause time']
			if dt < pausetime:
				thispause = pausetime - dt
				self.startTimer('drift pause')
				time.sleep(thispause)
				self.stopTimer('drift pause')

			## acquire next image at different correction channel than previous
			if corchan:
				corchan = 0
			else:
				corchan = 1
			imagedata = self.acquireImage(channel=corchan)
			if imagedata is None:
				return 'aborted', None, None
			self.logger.info('new image acquired')
			numdata = imagedata['image']
			binning = imagedata['camera']['binning']['x']
			t1 = imagedata['scope']['system time']
			self.correlator.insertImage(numdata)

			## do correlation
			try:
				self.startTimer('drift correlate')
				pc = self.correlator.phaseCorrelate()
				self.stopTimer('drift correlate')
				self.startTimer('drift peak')
				peak = self.peakfinder.subpixelPeak(newimage=pc)
				self.stopTimer('drift peak')
				rows,cols = self.peak2shift(peak, pc.shape)
			except Exception as e:
				self.logger.error(e)
				self.logger.warning('Failed correlation and/or peak finding, Set to zero shift')
				rows,cols = (0,0)
				peak = (0,0)
			dist = math.hypot(rows,cols)

			self.setImage(pc, 'Correlation')
			self.setTargets([(peak[1],peak[0])], 'Peak')

			self.logger.info('Pixel size is %s after binning' % (pixsize*binning))
			## calculate drift
			shrink_factor = imagefun.shrink_factor(numdata.shape)
			meters = dist * binning * pixsize * shrink_factor
			rowmeters = rows * binning * pixsize * shrink_factor
			colmeters = cols * binning * pixsize * shrink_factor
			# rely on system time of EM node
			seconds = t1 - t0
			self.logger.info('time %.2f' % seconds)
			lastdrift2 = lastdrift1
			lastdrift1 = current_drift
			current_drift = meters / seconds
			avgdrift = (current_drift + lastdrift1 + lastdrift2) / 3.0
			if lastdrift2 < 1.0e-4:
				self.logger.info('Drift rate: %.2e, average of last three: %.2e' % (current_drift, avgdrift,))
				drift_rate = avgdrift
			else:
				self.logger.info('Drift rate: %.2e' % (current_drift,))
				drift_rate = current_drift

			## publish scope and camera to be used with drift data
			scope = imagedata['scope']
			self.publish(scope, database=True, dbforce=True)
			camera = imagedata['camera']
			self.publish(camera, database=True, dbforce=True)

			d = leginondata.DriftData(session=self.session, rows=rows*shrink_factor, cols=cols*shrink_factor, interval=seconds, rowmeters=rowmeters, colmeters=colmeters, target=target, scope=scope, camera=camera)
			self.publish(d, database=True, dbforce=True)

			## t0 becomes t1 and t1 will be reset for next image
			t0 = t1

			# check both averaged drift rate and current drift rate.  Both need to be lower than the threshold
			if drift_rate < threshold and current_drift < threshold:
				return status, d, imagedata
			else:
				status = 'drifted'

			## check for abort
			if self.abortevent.isSet():
				return 'aborted', d, imagedata

			## check for timeout
			t = time.time()
			if t > timeout:
				return 'timeout', d, imagedata

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

		loop_interval = self.settings['measure drift interval']
		if loop_interval:
			self._loopMeasureDrift(pixsize)
		else:
			# do it once without logging
			current_drift = self._measureDrift(pixsize)

	def _loopMeasureDrift(self, pixsize):
		loop_interval = self.settings['measure drift interval']
		log_file = os.path.abspath('./drift_result.txt')
		self.logger.info('Writing into %s in nm/s' % log_file)
		## acquire images, measure drift
		self.abortevent.clear()
		while 1:
			if self.abortevent.isSet():
				self.logger.info('abort loop.')
				break
			t0 = time.time()
			datetimestr = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t0))
			current_drift = self._measureDrift(pixsize)
			if os.path.isfile(log_file):
				append_write = 'a'
			else:
				append_write = 'w'
			f = open('drift_result.txt', append_write)
			line = '%s\t%.3f\t%.3f\n' % (datetimestr, t0, current_drift*1e9)
			f.write(line)
			f.close()
			t1 = time.time()
			if t1-t0 < loop_interval:
				time.sleep(loop_interval - (t1-t0))

	def _measureDrift(self, pixsize):
		## acquire first image
		imagedata = self.acquireImage(0)
		if imagedata is None:
			self.logger.error('Failed acquiring image')
			return
		numdata = imagedata['image']
		t0 = imagedata['scope']['system time']
		self.correlator.insertImage(numdata)

		# make sure we have waited at least "pause time" before acquire
		t1 = self.instrument.tem.SystemTime
		dt = t1 - t0
		pausetime = self.settings['pause time']
		if dt < pausetime:
			thispause = pausetime - dt
			self.startTimer('drift pause')
			time.sleep(thispause)
			self.stopTimer('drift pause')
		
		## acquire next image
		imagedata = self.acquireImage(1)
		if imagedata is None:
			self.logger.error('Failed acquiring image')
			return
		numdata = imagedata['image']
		t1 = imagedata['scope']['system time']
		self.correlator.insertImage(numdata)

		## do correlation
		try:
			pc = self.correlator.phaseCorrelate()
			peak = self.peakfinder.subpixelPeak(newimage=pc)
		except Exception as e:
			self.logger.error(e)
			self.logger.warning('Correlation/PeakFinding error, assume no shift')
			peak = (0,0)
		rows,cols = self.peak2shift(peak, pc.shape)
		dist = math.hypot(rows,cols)

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
		return current_drift
