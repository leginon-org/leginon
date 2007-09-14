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
import time
from scipy import ndimage
pi = numpy.pi

def setImageFilename(imagedata, tiltnumber=None):
		acquisition.setImageFilename(imagedata)
		if tiltnumber is None:
			tiltnumber = imagedata['tiltnumber']
		if tiltnumber is not None:
			imagedata['filename'] = imagedata['filename'] + '_%02d' % (tiltnumber,)

def radians(degrees):
	return float(degrees) * pi / 180.0

def degrees(radians):
	return float(radians) * 180.0 / pi

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
		'stepsize': 15.0,
		'lowfilt': 0,
		'medfilt': 0,
		'minsize': 50,
		'maxsize': 0.8,
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
			#self.declareDrift('rct')
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
			#self.declaredrifteachtarget = True
			acquisition.Acquisition.processTargetList(self, tiltedtargetlist)
			#self.declaredrifteachtarget = False
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
		maxstepsize = radians(self.settings['stepsize'])
		#nsteps = float(self.settings['nsteps'])
		nsteps = math.ceil( abs( tiltrange / maxstepsize ) )
		#nsteps = abs(int(round(float(tiltrange) / float(maxstepsize))))
		self.logger.info('Number of tilt steps: %d' % nsteps)
		tilts = [tilt]
		if nsteps > 0:
			tilts = []
			stepsize = tiltrange / nsteps
			for i in range(1, nsteps+1):
				tilts.append(round(tilt0+i*stepsize,2))
		self.logger.info('Tilts: %s' % ([degrees(t) for t in tilts],))

		## loop through tilts
		medfilt = int(self.settings['medfilt'])
		lowfilt = float(self.settings['lowfilt'])
		imageold = image0
		arrayold = numpy.asarray(imageold['image'], dtype=numpy.float32)
		if medfilt > 1:
			arrayold = ndimage.median_filter(arrayold, size=medfilt)
		if lowfilt > 0:
			arrayold = ndimage.gaussian_filter(arrayold, lowfilt)
		runningresult = numpy.identity(3, numpy.float64)
		pausetime = int(self.settings['pause'])
		retries = 0
		i = 0.0
		#for tilt in tilts:
		while(i < nsteps):
			tilt = tilts[i]
			i += 1.0
			self.logger.info('Tilt: %s' % (degrees(tilt),))
			self.instrument.tem.StagePosition = {'a': tilt}
			time.sleep(pausetime)
			self.logger.info('Acquire intermediate tilted parent image')
			print 'acquire intertilt'
			dataclass = data.CorrectedCameraImageData
			imagenew = self.instrument.getData(dataclass)
			arraynew = numpy.asarray(imagenew['image'], dtype=numpy.float32)
			if medfilt > 1:
				arraynew = ndimage.median_filter(arraynew, size=medfilt)
			if lowfilt > 0:
				arraynew = ndimage.gaussian_filter(arraynew, lowfilt)
			self.setImage(arraynew, 'Image')
			self.setTargets([], 'Peak')


			print '============ Craig stuff ============'

			self.logger.info('Craig stuff')
			minsize = self.settings['minsize']
			maxsize = self.settings['maxsize']
			blur = 0
			sharpen = 0
			self.checkArrayMinMax(arrayold, arraynew)
			result = libCV.MatchImages(arrayold, arraynew, minsize, maxsize, blur, sharpen, 1, 1)

			check = self.checkLibCVResult(result)
			if check is False:
				self.logger.error("libCV failed: redoing tilt")
				#redo this tilt; becomes an infinite loop if the image goes black
				retries += 1
				if retries < 3:
					#reduce minsize and try again
					self.settings['minsize'] *= 0.95
					i -= 1.0
				continue
			print '============ Craig stuff done ============'

			prettyres = ( "libCV Matrix: [[ %.3f, %.3f ], [ %.3f, %.3f ], [ %.3f, %.3f ]] " % \
				results[0,0], results[0,1], results[1,0], results[1,1], results[2,0], results[2,1] )
			#self.logger.info('Matrix: %s' % (result,))
			self.logger.info(prettyres)

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
		imagedata = data.AcquisitionImageData(initializer=imageold, preset=image0['preset'], label=self.name,\
		 target=image0['target'], list=None, emtarget=image0['emtarget'], version=0, tiltnumber=self.tiltnumber)
		self.setTargets([], 'Peak')
		self.publishDisplayWait(imagedata)

		self.logger.info('Final Matrix: %s' % (runningresult,))
		return (runningresult, imagedata)

	def checkArrayMinMax(self, a1, a2):
		a1b = ndimage.median_filter(a1, size=3)
		min1 = ndimage.minimum(a1b)
		max1 = ndimage.maximum(a1b)
		if max1 - min1 < 10:
			self.logger.error("Old Image Range Error %d" % int(max1 - min1))
			return False
		a2b = ndimage.median_filter(a2, size=3)
		min2 = ndimage.minimum(a2b)
		max2 = ndimage.maximum(a2b)
		if max2 - min2 < 10:
			self.logger.error("New Image Range Error %d" % int(max2 - min2))
			return False
		return True

	def checkLibCVResult(self, result):
		if result[0][0] < 0.5 or result[1][1] < 0.5:
			self.logger.error("Bad libCV result: bad matrix")
			return False
		elif result[0][1] > 0.5 or result[1][0] > 0.5:
			self.logger.error('Bad libCV result: too much rotation')
			return False
		return True

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
		im = numpy.asarray(im, dtype=numpy.float32)
		medfilt = int(self.settings['medfilt'])
		lowfilt = float(self.settings['lowfilt'])
		if medfilt > 1:
			im = ndimage.median_filter(im, size=medfilt)
		if lowfilt > 0:
			im = ndimage.gaussian_filter(im, lowfilt)
		self.setImage(im)

		# find regions
		minsize = self.settings['minsize']
		maxsize = self.settings['maxsize']
		regions, image = libCV.FindRegions(im, minsize, maxsize, 0, 0, 1, 1)

		# this is copied from targetfinder:
		#regions,image = libCV.FindRegions(self.mosaicimage, minsize, maxsize, 0, 0, 0, 1, 5)
		n = len(regions)
		self.logger.info('Regions found: %s' % (n,))
		self.displayRegions(regions)

	def displayRegions(self, regions):
		targets = []
		limit = 1500
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
