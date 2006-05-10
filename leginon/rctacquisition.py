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

class RCTAcquisition(acquisition.Acquisition):
	panelclass = gui.wx.RCTAcquisition.Panel
	settingsclass = data.RCTAcquisitionSettingsData
	defaultsettings = acquisition.Acquisition.defaultsettings
	defaultsettings.update({'tilts': '(-45, 45)', 'stepsize': 10, 'sigma':0.5, 'minsize': 0.0015, 'maxsize': 0.9, 'minperiod': 0.02, 'minstable': 0.02})
	eventinputs = acquisition.Acquisition.eventinputs
	eventoutputs = acquisition.Acquisition.eventoutputs

	def __init__(self, id, session, managerlocation, **kwargs):
		acquisition.Acquisition.__init__(self, id, session, managerlocation, **kwargs)
		self.tiltnumber = None

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

	def tiltTargets(self, tilt0, tilt, tilt0targetlist):
		# find matrix
		image0 = tilt0targetlist['image']
		matrix,tiltedimagedata = self.trackStage(image0, tilt0, tilt)

		# create new target list adjusted for new tilt
		tilt0targets = self.researchTargets(list=tilt0targetlist, status='new')
		rows,cols = image0['camera']['dimension']['y'], image0['camera']['dimension']['x']
		tiltedtargetlist = self.newTargetList(image=tiltedimagedata)
		self.publish(tiltedtargetlist, database=True)
		displaytargets = []
		for tilt0target in tilt0targets:
			row = tilt0target['delta row'] + rows/2
			col = tilt0target['delta column'] + cols/2
			v = numarray.array((row,col,1))
			row2,col2,one = numarray.matrixmultiply(v, matrix)
			displaytargets.append((col2,row2))
			tiltedtarget = data.AcquisitionImageTargetData(initializer=tilt0target)
			tiltedtarget['delta row'] = row2 - rows/2
			tiltedtarget['delta column'] = col2 - cols/2
			tiltedtarget['list'] = tiltedtargetlist
			tiltedtarget['image'] = tiltedimagedata
			tiltedtarget['scope'] = tiltedimagedata['scope']
			tiltedtarget['version'] = 0
			self.publish(tiltedtarget, database=True)

		self.setTargets(displaytargets, 'Peak')

		return tiltedtargetlist

	def trackStage(self, image0, tilt0, tilt):
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
			print 'runningresult', runningresult

			imageold = imagenew
			arrayold = arraynew

		### copied from Acquisition.acquire:
		## store EMData to DB to prevent referencing errors
		self.publish(imageold['scope'], database=True)
		self.publish(imageold['camera'], database=True)

		## convert CameraImageData to AcquisitionImageData
		imagedata = data.AcquisitionImageData(initializer=imageold, preset=image0['preset'], label=self.name, target=image0['target'], list=None, emtarget=image0['emtarget'])
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
