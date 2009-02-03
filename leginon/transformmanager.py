#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import node
import event
import leginondata
from pyami import correlator, peakfinder
import calibrationclient
import math
import time
import threading
import presets
import copy
import EM
import gui.wx.DriftManager
import instrument
import acquisition
import rctacquisition

class TargetTransformer(object):
	def lookupMatrix(self, image):
		matrixquery = leginondata.TransformMatrixData()
		matrixquery['session'] = image['session']
		results = matrixquery.query()
		if not results:
			newmatrix = leginondata.TransformMatrixData()
			newmatrix['session'] = self.session
			newmatrix['matrix'] = numpy.identity(2)
			newmatrix.insert()
			results = [newmatrix]
	
		initialmatrix = None
		mymatrix = None
		for matrix in results:
			resultimage = matrix.special_getitem('image', dereference=False)
			if resultimage is None:
				initialmatrix = matrix
				break
			if resultimage.dbid == image.dbid:
				mymatrix = matrix
	
		if image is None:
			return initialmatrix
		else:
			return mymatrix
	
	def calculateMatrix(self, image1, image2):
		matrix = numpy.identity(2)
		return matrix
	
	def matrixTransform(self, target, matrix):
			row = target['delta row']
			row,col = numpy.dot((row,col), matrix['matrix'])
			newtarget = leginondata.AcquisitionImageTargetData(initializer=target)
			newtarget['version'] = matrix['image2']['version']
			newtarget['image'] = matrix['image2']
			newtarget['delta row'] = row
			newtarget['delta column'] = col
			newtarget['from target'] = target
			return newtarget
	
	def transformTarget(self, target):
		parentimage = target['image']
		matrix = self.lookupMatrix(parentimage)
		if parentimage is None:
			newtarget = self.matrixTransform(target, matrix)
			return newtarget
		if matrix is None:
			parenttarget = parentimage['target']
			newparenttarget = self.transformTarget(parenttarget)
			newparentimage = self.reacquire(newparenttarget)
			matrix = self.calculateMatrix(parentimage, newparentimage)
		newtarget = self.matrixTransform(target, matrix)
		return newtarget

class TransformManager(node.Node, TargetTransformer):
	panelclass = gui.wx.DriftManager.Panel
	settingsclass = leginondata.DriftManagerSettingsData
	defaultsettings = {
		'threshold': 3e-10,
		'pause time': 2.5,
		'camera settings':
			leginondata.CameraSettingsData(
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
	eventinputs = node.Node.eventinputs + presets.PresetsClient.eventinputs + [event.TransformTargetEvent]
	eventoutputs = node.Node.eventoutputs + presets.PresetsClient.eventoutputs + [event.TransformTargetDoneEvent]
	def __init__(self, id, session, managerlocation, **kwargs):
		node.Node.__init__(self, id, session, managerlocation, **kwargs)

		self.correlator = correlator.Correlator()
		self.peakfinder = peakfinder.PeakFinder()
		self.instrument = instrument.Proxy(self.objectservice, self.session,
																				self.panel)
		self.pixsizeclient = calibrationclient.PixelSizeCalibrationClient(self)
		self.presetsclient = presets.PresetsClient(self)
		self.addEventInput(event.TransformTargetEvent, self.handleTransformTargetEvent)

		self.abortevent = threading.Event()

		self.start()

	def reacquire(self, targetdata):
		oldtargetdata = targetdata['from target']
		aquery = leginondata.AcquisitionImageData(target=oldtargetdata)
		oldimage = aquery.query(readimages=False, results=1)
		emtarget = self.targetToEMTargetData(targetdata)
		presetname = oldimage['preset']['name']
		channel = int(oldimage['channel']==0)
		self.presetsclient.toScope(presetname, emtarget, keep_shift=False)
		targetdata = emtarget['target']
		self.instrument.setCorrectionChannel(channel)
		dataclass = leginondata.CorrectedCameraImageData
		imagedata = self.instrument.getData(dataclass)
		## convert CameraImageData to AcquisitionImageData
		dim = imagedata['camera']['dimension']
		pixels = dim['x'] * dim['y']
		pixeltype = str(imagedata['image'].dtype)
		imagedata = leginondata.AcquisitionImageData(initializer=imagedata, preset=presetdata, label=self.name, target=targetdata, list=self.imagelistdata, emtarget=emtarget, corrected=correctimage, pixels=pixels, pixeltype=pixeltype)
		imagedata['version'] = 0
		## store EMData to DB to prevent referencing errors
		self.publish(imagedata['scope'], database=True)
		self.publish(imagedata['camera'], database=True)
		return imagedata

	def handleTransformTargetEvent(self, ev):
		self.setStatus('processing')

		oldtarget = ev['target']

		newtarget = self.transformTarget(oldtarget)

		self.setStatus('idle')
		self.confirmEvent(ev)

	## much of the following method was stolen from acquisition.py
	def newImageVersion(self, oldimagedata, newimagedata, correct):
		## store EMData to DB to prevent referencing errors
		self.publish(newimagedata['scope'], database=True)
		self.publish(newimagedata['camera'], database=True)

		## convert CameraImageData to AcquisitionImageData
		newimagedata = leginondata.AcquisitionImageData(initializer=newimagedata)
		## then add stuff from old imagedata
		newimagedata['preset'] = oldimagedata['preset']
		newimagedata['label'] = oldimagedata['label']
		newimagedata['target'] = oldimagedata['target']
		newimagedata['list'] = oldimagedata['list']
		newimagedata['emtarget'] = oldimagedata['emtarget']
		newimagedata['version'] = oldimagedata['version'] + 1
		newimagedata['corrected'] = correct
		dim = newimagedata['camera']['dimension']
		newimagedata['pixels'] = dim['x'] * dim['y']
		newimagedata['pixeltype'] = str(newimagedata['image'].dtype)
		target = newimagedata['target']
		if target is not None and 'grid' in target and target['grid'] is not None:
			newimagedata['grid'] = target['grid']

		## set the 'filename' value
		if newimagedata['label'] == 'RCT':
			rctacquisition.setImageFilename(newimagedata)
		else:
			acquisition.setImageFilename(newimagedata)

		newimagedata.attachPixelSize()

		self.logger.info('Publishing new version of image...')
		self.publish(newimagedata, database=True, dbforce=True)
		return newimagedata

	def uiDeclareDrift(self):
		self.declareDrift('manual')

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
		if driftdata is not None:
			## use driftdata to set up scope and camera
			pname = driftdata['presetname']
			emtarget = driftdata['emtarget']
			threshold = driftdata['threshold']
			target = emtarget['target']
			self.presetsclient.toScope(pname, emtarget)
			presetdata = self.presetsclient.getCurrentPreset()
		else:
			target = None
			threshold = None

		## acquire images, measure drift
		self.abortevent.clear()
		time.sleep(self.settings['pause time']/2.0)	
		status,final,im = self.acquireLoop(target, threshold=threshold)
		if status == 'drifted':
			## declare drift above threshold
			self.declareDrift('threshold')

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
		self.instrument.setCorrectionChannel(channel)
		if correct:
			imagedata = self.instrument.getData(data.CorrectedCameraImageData)
		else:
			imagedata = self.instrument.getData(data.CameraImageData)
		if imagedata is not None:
			self.setImage(imagedata['image'], 'Image')
		self.stopTimer('drift acquire')
		return imagedata

	def acquireLoop(self, target=None, threshold=None):
		## acquire first image
		# make sure we have waited "pause time" before acquire the first image
		time.sleep(self.settings['pause time'])
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
		current_drift = 1.0e-3
		lastdrift1 = 1.0e-3
		lastdrift2 = 1.0e-3
		while 1:
			# make sure we have waited at least "pause time" before acquire
			t1 = self.instrument.tem.SystemTime
			dt = t1 - t0
			pausetime = self.settings['pause time']
			# make sure we have waited at least "pause time" before acquire
			# disabled but use the setting for before the first image.
#			if dt < pausetime:
			if False:
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
			dist = math.hypot(rows,cols)

			self.setImage(pc, 'Correlation')
			self.setTargets([(peak[1],peak[0])], 'Peak')

			## calculate drift 
			meters = dist * binning * pixsize
			rowmeters = rows * binning * pixsize
			colmeters = cols * binning * pixsize
			# rely on system time of EM node
			seconds = t1 - t0
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

			d = leginondata.DriftData(session=self.session, rows=rows, cols=cols, interval=seconds, rowmeters=rowmeters, colmeters=colmeters, target=target, scope=scope, camera=camera)
			self.publish(d, database=True, dbforce=True)

			## t0 becomes t1 and t1 will be reset for next image
			t0 = t1

			if drift_rate < threshold:
				return status, d, imagedata
			else:
				status = 'drifted'

			## check for abort
			if self.abortevent.isSet():
				return 'aborted', d, imagedata

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
		numdata = imagedata['image']
		t1 = imagedata['scope']['system time']
		self.correlator.insertImage(numdata)

		## do correlation
		pc = self.correlator.phaseCorrelate()
		peak = self.peakfinder.subpixelPeak(newimage=pc)
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

	def targetsToDatabase(self):
		for target in self.targetlist:
			self.publish(target, database=True)

