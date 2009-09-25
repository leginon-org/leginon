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
from pyami import correlator, peakfinder, ordereddict
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
import tiltcorrector

class InvalidStagePosition(Exception):
	pass

class Registration(object):
	def __init__(self, node):
		self.node = node
		self.stagetiltcorrector = tiltcorrector.VirtualStageTilter(self.node)

	def determinetransformtypes(self, image1, image2):
		ttype = []
		alpha1 = image1['scope']['stage position']['a']
		alpha2 = image2['scope']['stage position']['a']
		if abs(alpha1 - alpha2)* 180.0 / 3.14159 > 2:
			ttype.append('tilt')
		try:
			beta1 = image1['scope']['stage position']['b']
			beta2 = image2['scope']['stage position']['b']
			if abs(beta1 - beta2) * 180.0 / 3.14159 > 2:
				ttype.append('rotate')
		except:
			pass
		return ttype

	def undoTilt(self,imagedata):
		# matrix and shift returned from tiltcorrector is that for image transform
		untilted_array,image2by2matrix,imageshiftvector =self.stagetiltcorrector.getZeroTiltArray(imagedata)
		affinematrix = numpy.matrix(numpy.identity(3, numpy.float))
		affinematrix[:2,:2] = image2by2matrix
		# Matrix for target transform is the inverse of that for image transform 
		# without shift because the target is defined relative to center of the image
		return untilted_array,affinematrix.I

	def registerImageData(self,image1,image2):
		# return target transform matrix
		transformtypes = self.determinetransformtypes(image1,image2)
		prepmatrix1 = numpy.matrix(numpy.identity(3, numpy.float))
		prepmatrix2 = numpy.matrix(numpy.identity(3, numpy.float))
		array1 = image1['image']
		array2 = image2['image']
		for ttype in transformtypes:
			if ttype == 'tilt':
				self.node.logger.info('Virtual untilt images before registering')
				array1, untiltmatrix1 = self.undoTilt(image1)
				array2, untiltmatrix2 = self.undoTilt(image2)
				prepmatrix1 *= untiltmatrix1 
				prepmatrix2 *= untiltmatrix2 
		matrix = self.register(array1, array2)
		finalmatrix = matrix * prepmatrix1 * prepmatrix2.I
		return finalmatrix
			
	def register(self, array1, array2):
		raise NotImplementedError('define "register" method in a subclass of Registration')

class IdentityRegistration(Registration):
	'''Fake registration.  Always returns identity matrix'''
	def register(self, array1, array2):
		return numpy.matrix(numpy.identity(3, numpy.float))

class CorrelationRegistration(Registration):
	'''Register using peak found in phase correlation image'''
	def __init__(self, *args, **kwargs):
		super(CorrelationRegistration, self).__init__(*args, **kwargs)
		self.correlator = correlator.Correlator()
		self.peakfinder = peakfinder.PeakFinder()

	def register(self, array1, array2):
		self.correlator.setImage(0,array1)
		self.correlator.setImage(1,array2)
		corrimage = self.correlator.phaseCorrelate()
		self.node.setImage(corrimage, 'Correlation')
		peak = self.peakfinder.subpixelPeak(newimage=corrimage)
		self.node.setTargets([(peak[1],peak[0])], 'Peak')
		shift = correlator.wrap_coord(peak, corrimage.shape)
		matrix = numpy.matrix(numpy.identity(3, numpy.float))
		matrix[2,0] = shift[0]
		matrix[2,1] = shift[1]
		return matrix

class KeyPointsRegistration(Registration):
	def register(self, array1, array2):
		for minsize in (160,40,10):
			minsize = int(minsize * (array1.shape[0]/4096.0))
			resultmatrix = libCVwrapper.MatchImages(array1, array2, minsize=minsize, maxsize=0.9,  WoB=True, BoW=True)
			if abs(resultmatrix[0,0]) > 0.01 or abs(resultmatrix[0,1]) > 0.01:
				break
		return numpy.matrix(resultmatrix)

class LogPolarRegistration(Registration):
	def register(self, array1, array2):
		result = align.findRotationScaleTranslation(array1, array2)
		rotation, scale, shift, rsvalue, value = result
		matrix = numpy.matrix(numpy.identity(3, numpy.float))
		matrix[0,0] = scale*math.cos(rotation)
		matrix[0,1] = -scale*math.sin(rotation)
		matrix[1,0] = scale*math.sin(rotation)
		matrix[1,1] = scale*math.cos(rotation)
		matrix[2,0] = shift[0]
		matrix[2,1] = shift[1]
		return matrix

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
		## Debugging...
		print 'IMAGE DBID', image1.dbid
		print 'IMAGE PATH', image1.getpath()
		print 'IMAGE FILENAME', image1.filename()
		fileref = image1.special_getitem('image', dereference=False)
		import sinedon.newdict
		import numpy
		if isinstance(fileref, sinedon.newdict.FileReference):
			print 'FILEREF PATH', fileref.path
			print 'FILEREF FILENAME', fileref.filename
		elif isinstance(fileref, numpy.ndarray):
			print 'FILEREF ALREADY READ'
		## End debugging
		array1 = image1['image']
		array2 = image2['image']
		shape = array1.shape

		regtype = self.settings['registration']
		reg = self.registrations[regtype]
		self.logger.info('Calculating main transform. Registration: %s' % (regtype,))
		matrix = reg.registerImageData(image1,image2)
		print "---target transform matrix----"
		print matrix
		self.logger.info('Target transform matrix calculated')
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
		for t in alltargets:
			newt = self.matrixTransformOne(t, matrix, newimage)
			if t['number'] == target['number'] and t['status'] == target['status']:
				ret = newt
		return ret
	
	def matrixTransformOne(self, target, matrix,newimage=None):
		row = target['delta row']
		col = target['delta column']
		rowcolmatrix = numpy.dot((row,col,1), matrix)
		newtarget = leginondata.AcquisitionImageTargetData(initializer=target)
		# Fix here about version
		newtarget['image'] = newimage
		newtarget['delta row'] = rowcolmatrix[0,0]
		newtarget['delta column'] = rowcolmatrix[0,1]
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
		parentimage = target['image']
		matrix = self.lookupMatrix(parentimage)
		if parentimage is None:
			return target
		## check all transforms declared to decide on minimum mag
		## for now there is only one
		minimum_mag = self.settings['min mag']
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
				return None
			matrix = self.calculateMatrix(parentimage, newparentimage)
		newtarget = self.matrixTransform(target, matrix,newparentimage)
		return newtarget

class TransformManager(node.Node, TargetTransformer):
	panelclass = gui.wx.TransformManager.Panel
	settingsclass = leginondata.TransformManagerSettingsData
	defaultsettings = {
		'registration': 'correlation',
		'threshold': 3e-10,
		'pause time': 2.5,
		'min mag': 300,
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

		self.registrations = {
			'correlation': CorrelationRegistration(self),
			'keypoints': KeyPointsRegistration(self),
			'logpolar': LogPolarRegistration(self),
		}

		self.abortevent = threading.Event()

		self.start()

	def getRegistrationTypes(self):
		return self.registrations.keys()

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
		
		emtargetdata['target'] = targetdata
		## publish in DB because it will likely be needed later
		## when returning to the same target,
		## even after it is removed from memory
		self.publish(emtargetdata, database=True)
		return emtargetdata
	
	def reacquire(self, targetdata):
		if targetdata['fromtarget'] is None:
			oldtargetdata = targetdata
		else:
			oldtargetdata = targetdata['fromtarget']
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
		oldpresetdata = oldimage['preset']
		presetname = oldpresetdata['name']
		channel = int(oldimage['correction channel']==0)
		self.presetsclient.toScope(presetname, emtarget, keep_shift=False)
		targetdata = emtarget['target']
		imagedata = self.acquireCorrectedCameraImageData(channel)
		currentpresetdata = self.presetsclient.getCurrentPreset()
		## convert CameraImageData to AcquisitionImageData
		dim = imagedata['camera']['dimension']
		pixels = dim['x'] * dim['y']
		pixeltype = str(imagedata['image'].dtype)
		## Fix me: Not sure what image list should go in here nor naming of the file
		imagedata = leginondata.AcquisitionImageData(initializer=imagedata, preset=currentpresetdata, label=self.name, target=targetdata, list=oldimage['list'], emtarget=emtarget, pixels=pixels, pixeltype=pixeltype,grid=oldimage['grid'])
		version = self.recentImageVersion(oldimage)
		imagedata['version'] = version + 1
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
		self.setImage(imagedata['image'], 'Image')
		return imagedata

	def recentImageVersion(self, imagedata):
		# find most recent version of this image
		p = leginondata.PresetData(name=imagedata['preset']['name'])
		q = leginondata.AcquisitionImageData()
		q['session'] = imagedata['session']
		q['target'] = imagedata['target']
		q['list'] = imagedata['list']
		q['preset'] = p
		allimages = q.query()
		version = 0
		for im in allimages:
			if im['version'] > version:
				version = im['version']
		return version

	def handleTransformTargetEvent(self, ev):
		self.setStatus('processing')
		oldtarget = ev['target']
		level = ev['level']
		requestingnode = ev['node']
		newtarget = self.transformTarget(oldtarget, level)
		evt = event.TransformTargetDoneEvent()
		evt['target'] = newtarget
		evt['destination'] = requestingnode
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

	def acquireImage(self, channel=0, correct=True):
		self.startTimer('drift acquire')
		if correct:
			imagedata = self.acquireCorrectedCameraImageData(channel)
		else:
			imagedata = self.acquireCameraImageData()
		if imagedata is not None:
			self.setImage(imagedata['image'], 'Image')
		self.stopTimer('drift acquire')
		return imagedata

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
		#self.setTargets([(peak[1],peak[0])], 'Peak')

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

	def displayTarget(self, targetdata):
		halfrows = targetdata['image']['camera']['dimension']['y'] / 2
		halfcols = targetdata['image']['camera']['dimension']['x'] / 2
		drow = target['delta row']
		dcol = target['delta column']
		x = dcol + halfcols
		y = drow + halfrows
		disptarget = x,y
			
		self.setTargets([disptarget], 'Target')
