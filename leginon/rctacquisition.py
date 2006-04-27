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

class RCTAcquisition(acquisition.Acquisition):
	panelclass = gui.wx.RCTAcquisition.Panel
	settingsclass = data.RCTAcquisitionSettingsData
	defaultsettings = acquisition.Acquisition.defaultsettings
	defaultsettings.update({'tilt1': 0.0, 'tilt2': 0.0, 'sigma':0.5, 'minsize': 0.0015, 'maxsize': 0.9, 'minperiod': 0.02, 'minstable': 0.02})
	eventinputs = acquisition.Acquisition.eventinputs
	eventoutputs = acquisition.Acquisition.eventoutputs

	def __init__(self, id, session, managerlocation, **kwargs):
		acquisition.Acquisition.__init__(self, id, session, managerlocation, **kwargs)
		self.tiltnumber = None

	def setImageFilename(self, imagedata):
		acquisition.Acquisition.setImageFilename(self, imagedata)
		imagedata['filename'] = imagedata['filename'] + '_%02d' % (self.tiltnumber,)
		
	def processTargetList(self, newdata):
		'''
		We override this so we can process each target list twice
		'''
		# set tilt1 = tilt of parent image
		self.tiltnumber = 1
		image1 = newdata['image']
		tilt1 = image1['scope']['stage position']['a']
		self.logger.info('doing tilt 1 = %s degrees' % (tilt1*180/pi,))
		self.instrument.tem.StagePosition = {'a': tilt1}
		acquisition.Acquisition.processTargetList(self, newdata)

		tilt1targets = self.researchTargets(list=newdata, status='new')
		if not tilt1targets:
			return

		tilt2 = self.settings['tilt2'] * pi / 180.0
		self.tiltnumber = 2
		tilt2targetlist = self.tiltTargets(tilt1, tilt2, newdata)

		# set tilt2
		self.logger.info('doing tilt 2 = %s degrees' % (tilt2*180/pi,))
		self.instrument.tem.StagePosition = {'a': tilt2}
		acquisition.Acquisition.processTargetList(self, tilt2targetlist)

		self.logger.info('resetting tilt1')
		self.instrument.tem.StagePosition = {'a': tilt1}

	def tiltTargets(self, tilt1, tilt2, tilt1targetlist):
		# find matrix
		#stepsize = self.settings['stepsize'] * pi / 180.0
		stepsizedeg = self.settings['tilt1']
		stepsize = stepsizedeg * pi / 180
		image1 = tilt1targetlist['image']
		matrix,tilt2imagedata = self.trackStage(image1, tilt1, tilt2, stepsize)

		# create new target list adjusted for tilt2
		tilt1targets = self.researchTargets(list=tilt1targetlist, status='new')
		rows,cols = image1['camera']['dimension']['y'], image1['camera']['dimension']['x']
		tilt2targetlist = self.newTargetList(image=tilt2imagedata)
		self.publish(tilt2targetlist, database=True)
		displaytargets = []
		for tilt1target in tilt1targets:
			row = tilt1target['delta row'] + rows/2
			col = tilt1target['delta column'] + cols/2
			v = numarray.array((row,col,1))
			row2,col2,one = numarray.matrixmultiply(v, matrix)
			displaytargets.append((col2,row2))
			tilt2target = data.AcquisitionImageTargetData(initializer=tilt1target)
			tilt2target['delta row'] = row2 - rows/2
			tilt2target['delta column'] = col2 - cols/2
			tilt2target['list'] = tilt2targetlist
			tilt2target['image'] = tilt2imagedata
			tilt2target['scope'] = tilt2imagedata['scope']
			tilt2target['version'] = 0
			self.publish(tilt2target, database=True)

		self.setTargets(displaytargets, 'Peak')

		return tilt2targetlist

	def trackStage(self, image1, tilt1, tilt2, stepsize):
		#### copied from drift manager
		## go to state of image1
		## go through preset manager to ensure we follow the right
		## cycle
		self.logger.info('Returning to state of image1')
		presetname = image1['preset']['name']
		emtarget = image1['emtarget']
		self.presetsclient.toScope(presetname, emtarget)

		## calculate tilts
		tiltrange = tilt2 - tilt1
		nsteps = abs(int(round(float(tiltrange) / stepsize)))
		tilts = [tilt2]
		if nsteps > 0:
			tilts = []
			stepsize = float(tiltrange) / nsteps
			for i in range(1, nsteps+1):
				tilts.append(tilt1+i*stepsize)
		self.logger.info('Tilts: %s' % ([t*180/3.14159 for t in tilts],))

		## loop through tilts
		imageold = image1
		sigma = self.settings['sigma']
		arrayold = numarray.nd_image.gaussian_filter(imageold['image'], sigma)
		runningresult = numarray.identity(3, numarray.Float64)
		for tilt in tilts:
			self.logger.info('Tilt: %s' % (tilt*180/3.14159,))
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
		imagedata = data.AcquisitionImageData(initializer=imageold, preset=image1['preset'], label=self.name, target=image1['target'], list=None, emtarget=image1['emtarget'])
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
