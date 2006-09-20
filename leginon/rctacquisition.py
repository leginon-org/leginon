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
import mser
import numarray
import numarray.nd_image
pi = numarray.pi

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
	defaultsettings.update({'tilts': '(-45, 45)', 'stepsize': 10, 'sigma':0.5, 'minsize': 0.0015, 'maxsize': 0.9, 'minperiod': 0.02, 'minstable': 0.02})
	eventinputs = acquisition.Acquisition.eventinputs
	eventoutputs = acquisition.Acquisition.eventoutputs

	def __init__(self, id, session, managerlocation, **kwargs):
		acquisition.Acquisition.__init__(self, id, session, managerlocation, **kwargs)
		self.tiltnumber = 0

	def setImageFilename(self, imagedata):
		acquisition.Acquisition.setImageFilename(self, imagedata)
		imagedata['filename'] = imagedata['filename'] + '_%02d' % (self.tiltnumber,)

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
		for i,tilt in enumerate(tilts):
			self.tiltnumber = i

			## only make new targets if tilt is different than tilt0
			if tilt == tilt0:
				tiltedtargetlist = tilt0targetlist
			else:
				tiltedtargetlist = self.tiltTargets(tilt0, tilt, tilt0targetlist)

			self.logger.info('doing tilt %d = %s degrees' % (i, degrees(tilt),))
			self.instrument.tem.StagePosition = {'a': tilt}
			acquisition.Acquisition.processTargetList(self, tiltedtargetlist)

		self.logger.info('returning to tilt0')
		self.instrument.tem.StagePosition = {'a': tilt0}
		self.reportTargetListDone(tilt0targetlist, 'success')

	def transformPoints(self, matrix, points):
		newpoints = []
		for point in points:
			v = numarray.array((point[0],point[1],1))
			new0,new1,one = numarray.matrixmultiply(v, matrix)
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
		sigma = self.settings['sigma']
		arrayold = numarray.nd_image.gaussian_filter(imageold['image'], sigma)
		runningresult = numarray.identity(3, numarray.Float64)
		for tilt in tilts:
			self.logger.info('Tilt: %s' % (degrees(tilt),))
			self.instrument.tem.StagePosition = {'a': tilt}

			self.logger.info('Acquire intermediate tilted parent image')
			print 'acquire intertilt'
			dataclass = data.CorrectedCameraImageData
			imagenew = self.instrument.getData(dataclass)
			arraynew = numarray.nd_image.gaussian_filter(imagenew['image'], sigma)
			self.setImage(imagenew['image'].astype(numarray.Float32), 'Image')
			self.setTargets([], 'Peak')

			self.logger.info('Craig stuff')
			print 'Craig stuff'
			minsize = self.settings['minsize']
			maxsize = self.settings['maxsize']
			minperiod = self.settings['minperiod']
			minstable = self.settings['minstable']
			result = mser.matchImages(arrayold, arraynew, minsize, maxsize, minperiod, minstable)
			print 'Craig stuff done'
			self.logger.info('Matrix: %s' % (result,))

			runningresult = numarray.matrixmultiply(runningresult, result)

			self.transformTargets(runningresult, tilt0targets)

			print 'runningresult', runningresult

			imageold = imagenew
			arrayold = arraynew

		### copied from Acquisition.acquire:
		## store EMData to DB to prevent referencing errors
		self.publish(imageold['scope'], database=True)
		self.publish(imageold['camera'], database=True)

		## convert CameraImageData to AcquisitionImageData
		imagedata = data.AcquisitionImageData(initializer=imageold, preset=image0['preset'], label=self.name, target=image0['target'], list=None, emtarget=image0['emtarget'])
		self.setTargets([], 'Peak')
		self.publishDisplayWait(imagedata)
		
		self.logger.info('Final Matrix: %s' % (runningresult,))
		return (runningresult, imagedata)

	def alreadyAcquired(self, target, presetname):
		return False

	def testAcquire(self):
		im = self.acquireImage()
		if im is None:
			return

		# filter
		sigma = self.settings['sigma']
		im = numarray.nd_image.gaussian_filter(im, sigma)

		self.setImage(im)

		# find regions
		minsize = self.settings['minsize']
		maxsize = self.settings['maxsize']
		minperiod = self.settings['minperiod']
		minstable = self.settings['minstable']
		result = mser.findRegions(im, minsize, maxsize, minperiod, minstable)
		n = len(result)
		self.logger.info('Regions found: %s' % (n,))
		self.displayRegions(result)

	def displayRegions(self, regions):
		targets = []
		limit = 2000
		for i, region in enumerate(regions):
			if i > limit:
				break
			r,c = region[:2]
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
