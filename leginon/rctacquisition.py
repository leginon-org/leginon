#
# COPYRIGHT:
#	   The Leginon software is Copyright 2003
#	   The Scripps Research Institute, La Jolla, CA
#	   For terms of the license agreement
#	   see  http://ami.scripps.edu/software/leginon-license
#
import data
import acquisition
import gui.wx.RCTAcquisition
import libCV
import numpy
pi = numpy.pi

def setImageFilename(imagedata, tiltnumber=None):
		acquisition.setImageFilename(imagedata)
		if tiltnumber is None:
			tiltnumber = imagedata['tiltnumber']
		if tiltnumber is not None:
			imagedata['filename'] = imagedata['filename'] + '_%02d' % (tiltnumber,)

def radians(degrees):
	return degrees * pi / 180.0

def degrees(radians):
	return radians * 180.0 / pi

def corner(center, shape):
	return center[0] + shape[0]/2, center[1] + shape[1]/2

def center(corner, shape):
	return corner[0] - shape[0]/2, corner[1] - shape[1]/2

def corners(centers, shape):
	return [corner(x,shape) for x in centers]

def centers(corners, shape):
	return [center(x,shape) for x in corners]

def targetShape(target):
	dims = target['image']['camera']['dimension']
	return dims['y'],dims['x']

def transposePoints(points):
	return [(x,y) for y,x in points]

def targetPoint(target):
	return target['delta row'],target['delta column']

def targetPoints(targets):
	return map(targetPoint, targets)

class RCTAcquisition(acquisition.Acquisition):
	panelclass = gui.wx.RCTAcquisition.Panel
	settingsclass = data.RCTAcquisitionSettingsData
	defaultsettings = acquisition.Acquisition.defaultsettings
	defaultsettings.update({
		'tilts': '(-45, 45)',
		'stepsize': 10,
		'sigma':0.5,
		'minsize': 0.0015,
		'maxsize': 0.9,
		'blur': 0.0,
		'sharpen': 0.0,
		'drift threshold': 0.0,
		'drift preset': None,
		})
	eventinputs = acquisition.Acquisition.eventinputs
	eventoutputs = acquisition.Acquisition.eventoutputs

	def __init__(self, id, session, managerlocation, **kwargs):
		acquisition.Acquisition.__init__(self, id, session, managerlocation, **kwargs)
		self.tiltnumber = 0
		self.tiltseries = None

	def setImageFilename(self, imagedata):
		setImageFilename(imagedata, tiltnumber=self.tiltnumber)
		imagedata['tilt series'] = self.tiltseries

	def processTargetList(self, tilt0targetlist):
		'''
		We override this so we can process each target list for each tilt
		'''

		## return if no targets in list
		tilt0targets = self.researchTargets(list=tilt0targetlist, status='new')
		if not tilt0targets:
			self.reportTargetListDone(tilt0targetlist, 'success')
			return

		## list of tilts entered by user in degrees, converted to radians
		tiltstr = self.settings['tilts']
		try:
			tilts = eval(tiltstr)
		except:
			self.logger.error('Invalid tilt list')
			return
		tilts = map(radians, tilts)

		## parent image and tilt of parent image
		image0 = tilt0targetlist['image']
		tilt0 = image0['scope']['stage position']['a']

		## loop through each tilt
		focused = False
		for i,tilt in enumerate(tilts):
			self.tiltnumber = i

			## only make new targets if tilt is different than tilt0
			if tilt == tilt0:
				tiltedtargetlist = tilt0targetlist
			else:
				tiltedtargetlist = self.tiltTargets(tilt0, tilt, tilt0targetlist)

			self.logger.info('doing tilt %d = %s degrees' % (i, degrees(tilt),))
			self.instrument.tem.StagePosition = {'a': tilt}

			## drift check
			try:
				focustarget = self.getFocusTargets(tiltedtargetlist)[0]
			except:
				self.logger.error('Need at least one focus target to check drift')
				focustarget = None
			try:
				emtarget = self.targetToEMTargetData(focustarget)
			except:
				self.logger.error('EMTarget failed, check move type')
				emtarget = None
			try:
				presetname = self.settings['drift preset']
			except:
				self.logger.error('Need preset to check drift')
				presetname = None
			if None not in (focustarget, emtarget, presetname):
				threshold = self.settings['drift threshold']
				self.checkDrift(presetname, emtarget, threshold)

			## mark focus target done if already focused
			'''
			if focused:
				self.focusDone(tiltedtargetlist)
			'''

			acquisition.Acquisition.processTargetList(self, tiltedtargetlist)
			focused = True

		self.logger.info('returning to tilt0')
		self.instrument.tem.StagePosition = {'a': tilt0}
		self.reportTargetListDone(tilt0targetlist, 'success')

	def getFocusTargets(self, targetlistdata):
		targets = []
		targetlist = self.researchTargets(list=targetlistdata, type='focus')
		for targetdata in targetlist:
			if targetdata['status'] != 'done':
				targets.append(targetdata)
		return targets

	def focusDone(self, targetlistdata):
		self.logger.info('focus already done at previous tilt, forcing focus target status=done')
		targetlist = self.getFocusTargets(targetlistdata)
		for targetdata in targetlist:
				donetarget = data.AcquisitionImageTargetData(initializer=targetdata, status='done')
				self.publish(donetarget, database=True)

	def transformPoints(self, matrix, points):
		newpoints = []
		for point in points:
			v = numpy.array((point[0],point[1],1))
			new0,new1,one = numpy.dot(v, matrix)
			newpoints.append((new0,new1))
		return newpoints

	def transformTargets(self, matrix, targets):

		points = targetPoints(targets)
		shape = targetShape(targets[0])
		points = corners(points, shape)
		newpoints = self.transformPoints(matrix, points)
		centerpoints = centers(newpoints, shape)

		newtargets = []
		for centerpoint,target in zip(centerpoints,targets):
			tiltedtarget = data.AcquisitionImageTargetData(initializer=target)
			tiltedtarget['delta row'] = centerpoint[0]
			tiltedtarget['delta column'] = centerpoint[1]
			tiltedtarget['version'] = 0
			newtargets.append(tiltedtarget)

		displaypoints = transposePoints(newpoints)
		self.setTargets(displaypoints, 'Peak')

		return newtargets

	def tiltTargets(self, tilt0, tilt, tilt0targetlist):
		# find matrix
		image0 = tilt0targetlist['image']
		tilt0targets = self.researchTargets(list=tilt0targetlist, status='new')
		matrix,tiltedimagedata = self.trackStage(image0, tilt0, tilt, tilt0targets)

		# create new target list adjusted for new tilt
		self.transformTargets(matrix, tilt0targets)

		## publish everything
		tiltedtargetlist = self.newTargetList(image=tiltedimagedata)
		self.publish(tiltedtargetlist, database=True)
		tiltedtargets = self.transformTargets(matrix, tilt0targets)
		for tiltedtarget in tiltedtargets:
			tiltedtarget['list'] = tiltedtargetlist
			tiltedtarget['image'] = tiltedimagedata
			tiltedtarget['scope'] = tiltedimagedata['scope']
			self.publish(tiltedtarget, database=True)

		return tiltedtargetlist

	def trackStage(self, image0, tilt0, tilt, tilt0targets):
		stepsizedeg = self.settings['stepsize']
		stepsize = radians(stepsizedeg)

		#### copied from drift manager
		## go to state of image0
		## go through preset manager to ensure we follow the right
		## cycle
		self.logger.info('Returning to state of image0')
		presetname = image0['preset']['name']
		emtarget = image0['emtarget']
		self.presetsclient.toScope(presetname, emtarget)

		## calculate tilts
		tiltrange = tilt - tilt0
		nsteps = abs(int(round(float(tiltrange) / stepsize)))
		tilts = [tilt]
		if nsteps > 0:
			tilts = []
			stepsize = float(tiltrange) / nsteps
			for i in range(1, nsteps+1):
				tilts.append(tilt0+i*stepsize)
		self.logger.info('Tilts: %s' % ([degrees(t) for t in tilts],))

		## loop through tilts
		imageold = image0
		#sigma = self.settings['sigma']
		#arrayold = scipy.ndimage.gaussian_filter(imageold['image'], sigma)
		arrayold = imageold['image']
		runningresult = numpy.identity(3, numpy.float64)
		for tilt in tilts:
			self.logger.info('Tilt: %s' % (degrees(tilt),))
			self.instrument.tem.StagePosition = {'a': tilt}

			self.logger.info('Acquire intermediate tilted parent image')
			print 'acquire intertilt'
			dataclass = data.CorrectedCameraImageData
			imagenew = self.instrument.getData(dataclass)
			#arraynew = scipy.ndimage.gaussian_filter(imagenew['image'], sigma)
			arraynew = imagenew['image']
			self.setImage(imagenew['image'], 'Image')
			self.setTargets([], 'Peak')

			self.logger.info('Craig stuff')
			print 'Craig stuff'
			minsize = self.settings['minsize']
			maxsize = self.settings['maxsize']
			blur = self.settings['blur']
			sharpen = self.settings['sharpen']
			result = libCV.MatchImages(arrayold, arraynew, minsize, maxsize, blur, sharpen, 1, 1)
			print 'Craig stuff done'
			self.logger.info('Matrix: %s' % (result,))

			runningresult = numpy.dot(runningresult, result)

			self.transformTargets(runningresult, tilt0targets)

			print 'runningresult', runningresult

			imageold = imagenew
			arrayold = arraynew

		### copied from Acquisition.acquire:
		## store EMData to DB to prevent referencing errors
		self.publish(imageold['scope'], database=True)
		self.publish(imageold['camera'], database=True)

		## convert CameraImageData to AcquisitionImageData
		imagedata = data.AcquisitionImageData(initializer=imageold, preset=image0['preset'], label=self.name, target=image0['target'], list=None, emtarget=image0['emtarget'], version=0, tiltnumber=self.tiltnumber)
		self.setTargets([], 'Peak')
		self.publishDisplayWait(imagedata)

		self.logger.info('Final Matrix: %s' % (runningresult,))
		return (runningresult, imagedata)

	def alreadyAcquired(self, target, presetname):
		return False

	def getTiltSeries(self, targetdata):
		'''
		targetdata argument is target about to be acquired.  Find the tilt
		series that this new image will belong to if it exists, otherwise
		create a new tilt series.
		'''
		commontarget = targetdata['image']['target']
		targetnumber = targetdata['number']
		qimage1 = data.AcquisitionImageData(target=commontarget)
		qtarget = data.AcquisitionImageTargetData(image=qimage1, number=targetnumber)
		qimage2 = data.AcquisitionImageData(target=qtarget)
		images = self.research(qimage2, readimages=False)
		if images:
			tiltseries = images[0]['tilt series']
			defocus = images[0]['scope']['defocus']
		else:
			tiltseries = None
			defocus = None
		return tiltseries, defocus

	def moveAndPreset(self, presetdata, emtarget):
		'''
		extend Acquisition.moveAndPreset because additionally we need to
		return to the same defocus as the other images in the tilt series
		'''
		acquisition.Acquisition.moveAndPreset(self, presetdata, emtarget)
		targetdata = emtarget['target']
		tiltseries,defocus = self.getTiltSeries(targetdata)
		if tiltseries is None:
			self.tiltseries = data.TiltSeriesData()
			self.publish(self.tiltseries, database=True, dbforce=True)
		else:
			self.tiltseries = tiltseries
			self.logger.info('using defocus of first tilt at this target')
			self.instrument.tem.Defocus = defocus

	def testAcquire(self):
		im = self.acquireImage()
		if im is None:
			return

		# filter
		#sigma = self.settings['sigma']
		#im = scipy.ndimage.gaussian_filter(im, sigma)

		self.setImage(im)

		# find regions
		minsize = self.settings['minsize']
		maxsize = self.settings['maxsize']
		blur = self.settings['blur']
		sharpen = self.settings['sharpen']
		regions,image = libCV.FindRegions(im, minsize, maxsize, blur, sharpen, 1, 1)
		# this is copied from targetfinder:
		#regions,image = libCV.FindRegions(self.mosaicimage, minsize, maxsize, 0, 0, 0, 1, 5)
		n = len(regions)
		self.logger.info('Regions found: %s' % (n,))
		self.displayRegions(regions)

	def displayRegions(self, regions):
		targets = []
		limit = 2000
		for i,region in enumerate(regions):
			if i > limit:
				break
			r,c = region['regionEllipse'][:2]
			targets.append((c,r))
		self.setTargets(targets, 'Peak')
		
	def acquireImage(self):
		errstr = 'Acquire image failed: %s'
		if self.presetsclient.getCurrentPreset() is None:
			self.logger.error('Preset is unknown')
			return

		try:
			imagedata = self.instrument.getData(data.CorrectedCameraImageData)
		except:
			self.logger.error(errstr % 'unable to get corrected image')
			return

		if imagedata is None:
			self.logger.error('Acquire image failed')
			return

		return imagedata['image']
