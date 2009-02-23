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
from pyami import mrc,correlator, peakfinder, ordereddict
import calibrationclient
import math
import numpy
import time
import threading
import presets
import copy
import EM
import gui.wx.TransformManager
import instrument
import acquisition
import rctacquisition
import libCVwrapper
import align
import targethandler

class InvalidStagePosition(Exception):
	pass

class TargetTransformer(targethandler.TargetHandler):
	def __init__(self):
		targethandler.TargetHandler.__init__(self)

	def lookupMatrix(self, image):
		matrixquery = leginondata.TransformMatrixData()
		matrixquery['session'] = self.session
		results = matrixquery.query()
		if not results:
			newmatrix = leginondata.TransformMatrixData()
			newmatrix['session'] = self.session
			newmatrix['matrix'] = numpy.identity(3)
			newmatrix.insert()
			results = [newmatrix]
	
		initialmatrix = None
		mymatrix = None
		for matrix in results:
			resultimage = matrix.special_getitem('image1', dereference=False)
			if resultimage is None:
				initialmatrix = matrix['matrix']
				break
			if resultimage.dbid == image.dbid:
				mymatrix = matrix['matrix']
	
		if image is None:
			return initialmatrix
		else:
			return mymatrix

	def calculateMatrix(self, image1, image2):
		array1 = image1['image']
		array2 = image2['image']
		shape = array1.shape
		print image1['filename']
		print image2['filename']
		self.logger.info('Calculating main transform...')
		#if image1['scope']['magnification'] < 2000:
		if False:
			print "libcv"
			for minsize in (160,40,10):
				minsize = int(minsize * (shape[0]/4096.0))
				print minsize
				resultmatrix = libCVwrapper.MatchImages(array1, array2, minsize=minsize, maxsize=0.9,  WoB=True, BoW=True)
				if abs(resultmatrix[0,0]) > 0.01 or abs(resultmatrix[0,1]) > 0.01:
					break
			matrix = resultmatrix
		elif False:
			print "log-polar transform"
			result = align.findRotationScaleTranslation(array1, array2)
			rotation, scale, shift, rsvalue, value = result
			matrix = numpy.array([1.0,0.0,0.0,0.0,1.0,0.0,0.0,0.0,1.0])
			matrix = matrix.reshape((3,3))
			matrix[0,0] = scale*math.cos(rotation)
			matrix[0,1] = -scale*math.sin(rotation)
			matrix[1,0] = scale*math.sin(rotation)
			matrix[1,1] = scale*math.cos(rotation)
			matrix[2,0] = shift[0]
			matrix[2,1] = shift[1]
		else:
			print "correlator"
			matrix = numpy.array([1.0,0.0,0.0,0.0,1.0,0.0,0.0,0.0,1.0])
			matrix = matrix.reshape((3,3))
			c = correlator.Correlator()
			p = peakfinder.PeakFinder()
			c.setImage(0,array1)
			c.setImage(1,array2)
			corrimage = c.phaseCorrelate()
			mrc.write(corrimage,'corr.mrc')
			p.setImage(corrimage)
			peak = peakfinder.findPixelPeak(corrimage)
			shift = [0,0]
			for i in (0,1):
				if peak['pixel peak'][i] > shape[i]/2:
					shift[i] = peak['pixel peak'][i] - shape[i]
				else:
					shift[i] = peak['pixel peak'][i]
			matrix[2,0] = shift[0]
			matrix[2,1] = shift[1]
		print matrix
		matrixquery = leginondata.TransformMatrixData()
		matrixquery['session'] = self.session
		results = matrixquery.query()
		if not results:
			newmatrix = leginondata.TransformMatrixData()
			newmatrix['session'] = self.session
			newmatrix['image1'] = image1
			newmatrix['image2'] = image2
			newmatrix['matrix'] = matrix
			newmatrix.insert()
			results = [newmatrix]
	
		return matrix

	def recentTargetVersions(self, targetdata):
		# find all siblings of this target, but only most recent versions
		q = leginondata.AcquisitionImageTargetData()
		q['session'] = targetdata['session']
		q['image'] = targetdata['image']
		q['list'] = targetdata['list']
		alltargets = q.query()
		mostrecent = {}
		for t in alltargets:
			key = (t['number'],t['status'])
			if key in mostrecent:
				continue
			mostrecent[key] = t
		final = mostrecent.values()
		return final

	def matrixTransform(self, target, matrix, newimage=None):
		alltargets = self.recentTargetVersions(target)
		print 'TARGET', target['number'], target['version'], target['status'], target.dbid
		for t in alltargets:
			print 'T', t['number'], t['version'], t['status'], t.dbid
			newt = self.matrixTransformOne(t, matrix, newimage)
			if t['number'] == target['number'] and t['status'] == target['status']:
				ret = newt
		return ret
	
	def matrixTransformOne(self, target, matrix,newimage=None):
		row = target['delta row']
		col = target['delta column']
		row,col,one = numpy.dot((row,col,1), matrix)
		newtarget = leginondata.AcquisitionImageTargetData(initializer=target)
		# Fix here about version
		newtarget['image'] = newimage
		newtarget['delta row'] = row
		newtarget['delta column'] = col
		newtarget['fromtarget'] = target
		# newimagedata can be none if it is from a virtual grid for atlas
		if newimage is not None:
			newtarget['version'] = newimage['version']
			newtarget['scope'] = newimage['scope']
			newtarget['camera'] = newimage['camera']
			newtarget['preset'] = newimage['preset']
		newtarget.insert(force=True)
		return newtarget
	
	def transformTarget(self, target, level):
		if target is None:
			print 'TRANSFORMTARGET NONE'
		else:
			print 'TRANSFORMTARGET', target.dbid
		parentimage = target['image']
		if parentimage:
			print 'PARENTIMAGE', parentimage.dbid
		else:
			print 'PAENTIMAGE', parentimage
		matrix = self.lookupMatrix(parentimage)
		print 'MATRIX', matrix
		if parentimage is None:
			return target
			#newtarget = self.matrixTransform(target, matrix)
			print 'AAAAAAAAA'
			return newtarget
		## check all transforms declared to decide on minimum mag
		## for now there is only one
		minimum_mag = self.settings['min mag']
		print 'PARENTIMAGE PRESET', parentimage['preset']['name'], parentimage['preset']['magnification']
		if parentimage['preset']['magnification'] < minimum_mag:
			self.logger.info('not transforming target because parent image has low mag')
			return target
		if matrix is None:
			parenttarget = parentimage['target']
			if level == 'all':
				newparenttarget = self.transformTarget(parenttarget, level)
			elif level == 'one':
				newparenttarget = parenttarget
			newparentimage = self.reacquire(newparenttarget)
			if newparentimage is None:
				print 'BBBBBBBB'
				return None
			matrix = self.calculateMatrix(parentimage, newparentimage)
		print parentimage.dbid,newparentimage.dbid
		newtarget = self.matrixTransform(target, matrix,newparentimage)
		print 'CCCCCCC'
		return newtarget

class TransformManager(node.Node, TargetTransformer):
	panelclass = gui.wx.TransformManager.Panel
	settingsclass = leginondata.TransformManagerSettingsData
	defaultsettings = {
		'threshold': 3e-10,
		'pause time': 2.5,
		'min mag': 2000,
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
		TargetTransformer.__init__(self)

		self.correlator = correlator.Correlator()
		self.peakfinder = peakfinder.PeakFinder()
		self.instrument = instrument.Proxy(self.objectservice, self.session,
																				self.panel)
		self.calclients = ordereddict.OrderedDict()
		self.calclients['image shift'] = calibrationclient.ImageShiftCalibrationClient(self)
		self.calclients['stage position'] = calibrationclient.StageCalibrationClient(self)
		self.calclients['modeled stage position'] = calibrationclient.ModeledStageCalibrationClient(self)
		self.calclients['image beam shift'] = calibrationclient.ImageBeamShiftCalibrationClient(self)
		self.calclients['beam shift'] = calibrationclient.BeamShiftCalibrationClient(self)
		self.pixsizeclient = calibrationclient.PixelSizeCalibrationClient(self)
		self.presetsclient = presets.PresetsClient(self)
		self.addEventInput(event.TransformTargetEvent, self.handleTransformTargetEvent)

		self.abortevent = threading.Event()

		self.start()

	def validateStagePosition(self, stageposition):
		## check for out of stage range target
		stagelimits = {
			'x': (-9.9e-4, 9.9e-4),
			'y': (-9.9e-4, 9.9e-4),
		}
		for axis, limits in stagelimits.items():
			if stageposition[axis] < limits[0] or stageposition[axis] > limits[1]:
				pstr = '%s: %g' % (axis, stageposition[axis])
				messagestr = 'Aborting target: stage position %s out of range' % pstr
				self.logger.info(messagestr)
				raise InvalidStagePosition(messagestr)

	def targetToEMTargetData(self, targetdata,movetype):
		'''
		copied from acquisition but get move type from old emtarget
		'''
		emtargetdata = leginondata.EMTargetData()
		if targetdata is not None:
			# get relevant info from target data
			targetdeltarow = targetdata['delta row']
			targetdeltacolumn = targetdata['delta column']
			origscope = targetdata['scope']
			targetscope = leginondata.ScopeEMData(initializer=origscope)
			## copy these because they are dictionaries that could
			## otherwise be shared (although transform() should be
			## smart enough to create copies as well)
			targetscope['stage position'] = dict(origscope['stage position'])
			targetscope['image shift'] = dict(origscope['image shift'])
			targetscope['beam shift'] = dict(origscope['beam shift'])

			oldpreset = targetdata['preset']

			zdiff = 0.0
			### simulated target does not require transform
			if targetdata['type'] == 'simulated':
				newscope = origscope
			else:
				targetcamera = targetdata['camera']
		
				## to shift targeted point to center...
				deltarow = -targetdeltarow
				deltacol = -targetdeltacolumn
		
				pixelshift = {'row':deltarow, 'col':deltacol}
				print "target pixel shift, ,movetype",pixelshift,movetype
				## figure out scope state that gets to the target
				calclient = self.calclients[movetype]
				try:
					newscope = calclient.transform(pixelshift, targetscope, targetcamera)
				except calibrationclient.NoMatrixCalibrationError, e:
					m = 'No calibration for acquisition move to target: %s'
					self.logger.error(m % (e,))
					raise NoMoveCalibration(m)

				## if stage is tilted and moving by image shift,
				## calculate z offset between center of image and target
				if movetype in ('image shift','image beam shift','beam shift') and abs(targetscope['stage position']['a']) > 0.02:
					calclient = self.calclients['stage position']
					try:
						tmpscope = calclient.transform(pixelshift, targetscope, targetcamera)
					except calibrationclient.NoMatrixCalibrationError:
						message = 'No stage calibration for z measurement'
						self.logger.error(message)
						raise NoMoveCalibration(message)
					ydiff = tmpscope['stage position']['y'] - targetscope['stage position']['y']
					zdiff = ydiff * numpy.sin(targetscope['stage position']['a'])
	
			### check if stage position is valid
			if newscope['stage position']:
				self.validateStagePosition(newscope['stage position'])
	
			emtargetdata['preset'] = oldpreset
			emtargetdata['movetype'] = movetype
			emtargetdata['image shift'] = dict(newscope['image shift'])
			emtargetdata['beam shift'] = dict(newscope['beam shift'])
			emtargetdata['stage position'] = dict(newscope['stage position'])
			emtargetdata['delta z'] = zdiff
		
		print	'stage position', emtargetdata['stage position']

		emtargetdata['target'] = targetdata
		print "TARGETtoEMTARGET",targetdata.dbid
		## publish in DB because it will likely be needed later
		## when returning to the same target,
		## even after it is removed from memory
		self.publish(emtargetdata, database=True)
		print "EMTARGETTARGET",emtargetdata['target'].dbid
		return emtargetdata
	
	def reacquire(self, targetdata):
		print "REACQUIRE START",targetdata.dbid
		if targetdata['fromtarget'] is None:
			oldtargetdata = targetdata
		else:
			oldtargetdata = targetdata['fromtarget']
		print "REACQUIRE OLDTARGET",oldtargetdata.dbid
		aquery = leginondata.AcquisitionImageData(target=oldtargetdata)
		results = aquery.query(readimages=False, results=1)
		if len(results) > 0:
			oldimage = results[0]
		else:
			aquery = leginondata.AcquisitionImageData(target=targetdata)
			results = aquery.query(readimages=False, results=1)
			oldimage = results[0]
		oldemtarget = oldimage['emtarget']
		movetype = oldemtarget['movetype']
		try:
			emtarget = self.targetToEMTargetData(targetdata,movetype)
		except InvalidStagePosition:
			self.logger.error('Invalid new emtarget')
			return None
		presetdata = oldimage['preset']
		presetname = presetdata['name']
		channel = int(oldimage['correction channel']==0)
		self.presetsclient.toScope(presetname, emtarget, keep_shift=False)
		targetdata = emtarget['target']
		print "REACQUIRE TARGET",targetdata.dbid
		self.instrument.setCorrectionChannel(channel)
		dataclass = leginondata.CorrectedCameraImageData
		imagedata = self.instrument.getData(dataclass)
		## convert CameraImageData to AcquisitionImageData
		dim = imagedata['camera']['dimension']
		pixels = dim['x'] * dim['y']
		pixeltype = str(imagedata['image'].dtype)
		## Fix me: Not sure what image list should go in here nor naming of the file
		imagedata = leginondata.AcquisitionImageData(initializer=imagedata, preset=presetdata, label=self.name, target=targetdata, list=oldimage['list'], emtarget=emtarget, corrected=True, pixels=pixels, pixeltype=pixeltype)
		version = oldimage['version']+1
		imagedata['version'] = version
		## set the 'filename' value
		if imagedata['label'] == 'RCT':
			rctacquisition.setImageFilename(imagedata)
		else:
			acquisition.setImageFilename(imagedata)
		## store EMData to DB to prevent referencing errors
		self.publish(imagedata['scope'], database=True)
		self.publish(imagedata['camera'], database=True)
		self.logger.info('Publishing new transformed image...')
		self.publish(imagedata, database=True)
		print "REACQUIRE IMAGE",imagedata.dbid
		self.setImage(imagedata['image'], 'Image')
		return imagedata

	def handleTransformTargetEvent(self, ev):
		self.setStatus('processing')
		oldtarget = ev['target']
		level = ev['level']
		newtarget = self.transformTarget(oldtarget, level)
		evt = event.TransformTargetDoneEvent()
		evt['target'] = newtarget
		self.outputEvent(evt)
		self.setStatus('idle')

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
		self.declareTransform('manual')

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
			imagedata = self.instrument.getData(leginondata.CorrectedCameraImageData)
		else:
			imagedata = self.instrument.getData(leginondata.CameraImageData)
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

