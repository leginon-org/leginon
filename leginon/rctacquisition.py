#
# COPYRIGHT:
#	   The Leginon software is Copyright 2003
#	   The Scripps Research Institute, La Jolla, CA
#	   For terms of the license agreement
#	   see  http://ami.scripps.edu/software/leginon-license
#
import leginondata
import acquisition
import gui.wx.RCTAcquisition
import libCVwrapper
import numpy
import time
import math
import pyami.quietscipy
from scipy import ndimage
#from apTilt import apTiltShift
pi = numpy.pi

#====================
def setImageFilename(imagedata, tiltnumber=None):
		acquisition.setImageFilename(imagedata)
		if tiltnumber is None:
			tiltnumber = imagedata['tiltnumber']
		if tiltnumber is not None:
			imagedata['filename'] = imagedata['filename'] + '_%02d' % (tiltnumber,)

#====================
def radians(degrees):
	return float(degrees) * pi / 180.0

#====================
def degrees(radians):
	return float(radians) * 180.0 / pi

#====================
def sign(x):
	if abs(x) < 0.017:
		return 0
	return int(abs(x)/x)

#====================
def corner(center, shape):
	return center[0] + shape[0]/2, center[1] + shape[1]/2

#====================
def center(corner, shape):
	return corner[0] - shape[0]/2, corner[1] - shape[1]/2

#====================
def corners(centers, shape):
	return [corner(x,shape) for x in centers]

#====================
def centers(corners, shape):
	return [center(x,shape) for x in corners]

#====================
def targetShape(target):
	dims = target['image']['camera']['dimension']
	return dims['y'],dims['x']

#====================
def transposePoints(points):
	return [(x,y) for y,x in points]

#====================
def targetPoint(target):
	return target['delta row'],target['delta column']

#====================
def targetPoints(targets):
	return map(targetPoint, targets)

#====================
#====================
class RCTAcquisition(acquisition.Acquisition):
	panelclass = gui.wx.RCTAcquisition.Panel
	settingsclass = leginondata.RCTAcquisitionSettingsData
	defaultsettings = acquisition.Acquisition.defaultsettings
	defaultsettings.update({
		'tilts': '(-45, 45)',
		'stepsize': 42.0,
		'pause': 1.0,
		'lowfilt': 1.0,
		'medfilt': 2,
		'minsize': 50,
		'maxsize': 0.8,
		'drift threshold': 0.0,
		'drift preset': None,
		})
	eventinputs = acquisition.Acquisition.eventinputs
	eventoutputs = acquisition.Acquisition.eventoutputs

	#====================
	def __init__(self, id, session, managerlocation, **kwargs):
		acquisition.Acquisition.__init__(self, id, session, managerlocation, **kwargs)
		self.tiltnumber = 0
		self.tiltseries = None

	#====================
	def setImageFilename(self, imagedata):
		setImageFilename(imagedata, tiltnumber=self.tiltnumber)
		imagedata['tilt series'] = self.tiltseries

	#====================
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
		## check for singular value
		if isinstance(tilts, float) or isinstance(tilts, int):
			tilts = (tilts,)
		## convert to radians
		tilts = map(radians, tilts)

		## parent image and tilt of parent image
		image0 = tilt0targetlist['image']
		tilt0 = image0['scope']['stage position']['a']

		## loop through each tilt
		focused = False
		for i,tilt in enumerate(tilts):
			if self.player.state() == 'stop':
				break
			self.tiltnumber = i

			## only make new targets if tilt is different than tilt0
			if degrees(abs(tilt - tilt0)) < 0.5:
				tiltedtargetlist = tilt0targetlist
			else:
				tiltedtargetlist = self.tiltTargets(tilt0, tilt, tilt0targetlist)
			if tiltedtargetlist is None:
				self.reportTargetListDone(tilt0targetlist, 'failure')
				return

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
			self.setTargets([], 'Peak')
			acquisition.Acquisition.processTargetList(self, tiltedtargetlist)
			#self.declaredrifteachtarget = False
			focused = True

		self.logger.info('returning to tilt0')
		self.instrument.tem.StagePosition = {'a': tilt0}
		self.reportTargetListDone(tilt0targetlist, 'success')

	#====================
	def getFocusTargets(self, targetlistdata):
		targets = []
		targetlist = self.researchTargets(list=targetlistdata, type='focus')
		for targetdata in targetlist:
			if targetdata['status'] != 'done':
				targets.append(targetdata)
		return targets

	#====================
	def focusDone(self, targetlistdata):
		self.logger.info('focus already done at previous tilt, forcing focus target status=done')
		targetlist = self.getFocusTargets(targetlistdata)
		for targetdata in targetlist:
				donetarget = leginondata.AcquisitionImageTargetData(initializer=targetdata, status='done')
				self.publish(donetarget, database=True)

	#====================
	def transformPoints(self, matrix, points):
		newpoints = []
		for point in points:
			v = numpy.array((point[0],point[1],1))
			new0,new1,one = numpy.dot(v, matrix)
			newpoints.append((new0,new1))
		return newpoints

	#====================
	def transformTargets(self, matrix, targets):

		points = targetPoints(targets)
		shape = targetShape(targets[0])
		points = corners(points, shape)
		newpoints = self.transformPoints(matrix, points)
		centerpoints = centers(newpoints, shape)

		newtargets = []
		for centerpoint,target in zip(centerpoints,targets):
			tiltedtarget = leginondata.AcquisitionImageTargetData(initializer=target)
			tiltedtarget['delta row'] = centerpoint[0]
			tiltedtarget['delta column'] = centerpoint[1]
			tiltedtarget['version'] = 0
			newtargets.append(tiltedtarget)

		displaypoints = transposePoints(newpoints)
		self.setTargets(displaypoints, 'Peak')

		return newtargets

	#====================
	def tiltTargets(self, tilt0, tilt, tilt0targetlist):
		# find matrix
		image0 = tilt0targetlist['image']
		tilt0targets = self.researchTargets(list=tilt0targetlist, status='new')
		matrix,tiltedimagedata = self.trackStage(image0, tilt0, tilt, tilt0targets)
		if matrix is None:
			return None

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

	#====================
	def trackStage(self, image0, tilt0, tilt, tilt0targets):
		#import pprint
		#print "SETTINGS:"
		#pprint.pprint(self.settings)

		self.logger.info('Returning to state of image0')
		presetname = image0['preset']['name']
		emtarget = image0['emtarget']
		pausetime = self.settings['pause']
		self.presetsclient.toScope(presetname, emtarget)
		### reset the tilt, just in case user changed it while picking targets
		self.instrument.tem.StagePosition = {'a': tilt0}
		if pausetime > 0.1:
			self.logger.info('Pausing %.1f seconds' %(pausetime,))
			time.sleep(pausetime)

		### calculate tilt steps
		maxstepsize = radians(self.settings['stepsize'])
		tilts = self.calculateTiltSteps(tilt0, tilt, maxstepsize)
		self.logger.info('Tilts: %s' % ([("%.1f"%degrees(t)) for t in tilts],))

		## filter image
		medfilt = int(self.settings['medfilt'])
		lowfilt = float(self.settings['lowfilt'])
		imageold = image0
		arrayold = numpy.asarray(imageold['image'], dtype=numpy.float32)
		if medfilt > 1:
			arrayold = ndimage.median_filter(arrayold, size=medfilt)
		if lowfilt > 0:
			arrayold = ndimage.gaussian_filter(arrayold, lowfilt)
		self.setImage(arrayold, 'Image')
		runningresult = numpy.identity(3, numpy.float32)
		self.transformTargets(runningresult, tilt0targets)
		retries = 0

		#for tilt in tilts:
		### use while loop so we can backtrack
		i = 0
		while i < len(tilts)-1:
			i+=1
			tilt = float("%.3f"%tilts[i])
			self.logger.info('Going to tilt angle: %.2f' % (degrees(tilt),))
			self.instrument.tem.StagePosition = {'a': tilt}
			if pausetime > 0.1:
				self.logger.info('Pausing %.1f seconds' %(pausetime,))
				time.sleep(pausetime)
			self.logger.info('Acquire intermediate tilted parent image')
			#print 'acquire intertilt'
			imagenew = self.acquireCorrectedCameraImageData()
			arraynew = numpy.asarray(imagenew['image'], dtype=numpy.float32)
			if medfilt > 1:
				arraynew = ndimage.median_filter(arraynew, size=medfilt)
			if lowfilt > 0:
				arraynew = ndimage.gaussian_filter(arraynew, lowfilt)
			self.setImage(arraynew, 'Image')

			print '============ Craig stuff ============'

			self.logger.info('Craig\'s libCV stuff')
			minsize = self.settings['minsize']
			maxsize = self.settings['maxsize']
			libCVwrapper.checkArrayMinMax(self, arrayold, arraynew)
			result = libCVwrapper.MatchImages(arrayold, arraynew, minsize, maxsize)
			#difftilt = degrees(abs(tilts[int(i)])-abs(tilts[int(i-1)]))
			#result = self.apTiltShiftMethod(arrayold, arraynew, difftilt)

			self.logger.info("result matrix= "+str(numpy.asarray(result*100, dtype=numpy.int8).ravel()))

			check = libCVwrapper.checkLibCVResult(self, result)
			if check is False:
				self.logger.warning("libCV failed: redoing tilt %.2f"%(tilt,))
				### redo this tilt; becomes an infinite loop if the image goes black
				retries += 1
				if retries <= 2:
					### reduce minsize and try again
					self.settings['minsize'] *= 0.95
					if i == len(tilts)-1:
						### maybe the tilt angle is too high, reduce max angle by 5 percent
						tilts[len(tilts)-1] *= 0.95
					i -= 1
				else:
					retries = 0
					print "Tilt libCV FAILED"
					self.logger.error("libCV failed: giving up")
					return None, None
				continue
			else:
				retries = 0			
			print '============ Craig stuff done ============'

			self.logger.info("result matrix= "+str(numpy.asarray(result*100, dtype=numpy.int8).ravel()))
			self.logger.info( "Inter Matrix: "+libCVwrapper.affineToText(result) )

			runningresult = numpy.dot(runningresult, result)
			self.transformTargets(runningresult, tilt0targets)
			self.logger.info( "Running Matrix: "+libCVwrapper.affineToText(runningresult) )
			self.logger.info("running result matrix= "+str(numpy.asarray(runningresult*100, dtype=numpy.int8).ravel()))
			imageold = imagenew
			arrayold = arraynew

		### copied from Acquisition.acquire:
		## store EMData to DB to prevent referencing errors
		self.publish(imageold['scope'], database=True)
		self.publish(imageold['camera'], database=True)

		## convert CameraImageData to AcquisitionImageData
		dim = image0['camera']['dimension']
		pixels = dim['x'] * dim['y']
		pixeltype = str(image0['image'].dtype)
		imagedata = leginondata.AcquisitionImageData(initializer=imageold, preset=image0['preset'], label=self.name,
			target=image0['target'], list=None, emtarget=image0['emtarget'], 
			version=0, tiltnumber=self.tiltnumber, pixels=pixels, pixeltype=pixeltype)
		self.setTargets([], 'Peak')
		self.publishDisplayWait(imagedata)

		self.logger.info( "FINAL Matrix: "+libCVwrapper.affineToText(runningresult) )
		#self.logger.info('Final Matrix: %s' % (runningresult,))
		return (runningresult, imagedata)

	#====================
	def calculateTiltSteps(self, tilt0, tilt, maxstepsize):
		### warn if signs are different
		if sign(tilt0)*sign(tilt) < 0:
			self.logger.warning('Starting tilt %.1f and final tilt %.1f have opposite signs' 
			% (degrees(tilt0), degrees(tilt)))

		### calculate initial cosines and sort by size
		self.logger.info('Starting at tilt %.1f going to tilt %.1f with max step size %.1f' 
			% (degrees(tilt0), degrees(tilt), degrees(maxstepsize)))
		mincos = min(math.cos(tilt0), math.cos(tilt))
		maxcos = max(math.cos(tilt0), math.cos(tilt))

		### set minimum number of steps
		maxangle = degrees(max(abs(tilt0),abs(tilt)))
		diffangle = degrees(abs(tilt0 - tilt))
		if maxangle < 20 or diffangle < 10:
			# no intermediate step required
			nsteps = 0
		else:
			# always have at least one intermediate step
			nsteps = 1
		self.logger.info('Minimum number of steps: %d (%.1f, %.1f)' % (nsteps+1, maxangle, diffangle))

		### increase the number of steps until bigstepsize > maxstepsize
		maxstepsize = radians(self.settings['stepsize'])
		bigstepsize = 4.0
		while bigstepsize > maxstepsize and nsteps < 6:
			nsteps += 1
			### find the angles
			coslist = [mincos]
			for i in range(nsteps):
				thiscos = (maxcos-mincos)*(i+1)/float(nsteps)+mincos
				coslist.append(thiscos)

			# what is the biggest step?
			bigstepsize = 0
			for i in range(len(coslist)-1):
				stepsize = math.acos(coslist[i])-math.acos(coslist[i+1])
				bigstepsize = max(stepsize,bigstepsize)
			#self.logger.info('%d: %.1f max, tilts: %s' % (nsteps, degrees(bigstepsize),
			#	 [("%.1f"%degrees(math.acos(c))) for c in coslist],))
			#time.sleep(0.2)

		### look at final values
		self.logger.info('Number of tilt steps: %d' % nsteps)
		if nsteps > 5:
			self.logger.warning("More than 5 tilt steps, increase your "
				+"max step size to at least %.1f"%(degrees(bigstepsize)))

		### convert the cosines into angles
		tilts = []
		for cosval in coslist:
			tilts.append(math.acos(cosval))

		### swap the order if we have the wrong start
		if abs(abs(tilt0) - tilts[0]) > 0.1:
			tilts.reverse()

		tilts = numpy.asarray(tilts, dtype=numpy.float32)
		### if angle < 15, sign doesn't matter
		if (abs(degrees(tilt)) > 19 and sign(tilt) < 0) or (abs(degrees(tilt)) < 20 and sign(tilt0) < 0):
			tilts *= -1.0

		### reset start and stop
		tilts[0] = tilt0
		tilts[len(tilts)-1] = tilt

		return tilts

	#====================
	def apTiltShiftMethod(self, arrayold, arraynew, difftilt):
		### pre-filter images
		print "difftilt=", difftilt
		#print arrayold.shape, arraynew.shape, difftilt
		bestsnr = 0
		bestangle = None
		self.logger.info('Using cross-correlation method to find matrix')
		for angle in [-14, -7, 0, 7, 14]:
			shift, xfactor, snr = apTiltShift.getTiltedRotateShift(arrayold, arraynew, difftilt, angle, msg=False)
			if snr > bestsnr:
				bestsnr = snr
				bestangle = angle
				print "best tilt axis angle=", bestsnr, bestangle, shift
				self.logger.info('best tilt axis angle = %.2f (snr = %.2f; shift = %s)'%(bestangle, bestsnr, shift))
		for angle in [bestangle-5, bestangle-3, bestangle+3, bestangle+5]:
			shift, xfactor, snr = apTiltShift.getTiltedRotateShift(arrayold, arraynew, difftilt, angle, msg=False)
			if snr > bestsnr:
				bestsnr = snr
				bestangle = angle
				print "best tilt axis angle=", bestsnr, bestangle, shift
				self.logger.info('best tilt axis angle = %.2f (snr = %.2f; shift = %s)'%(bestangle, bestsnr, shift))
		for angle in [bestangle-2, bestangle-1, bestangle+1, bestangle+2]:
			shift, xfactor, snr = apTiltShift.getTiltedRotateShift(arrayold, arraynew, difftilt, angle, msg=False)
			if snr > bestsnr:
				bestsnr = snr
				bestangle = angle
				print "best tilt axis angle=", bestsnr, bestangle, shift
				self.logger.info('best tilt axis angle = %.2f (snr = %.2f; shift = %s)'%(bestangle, bestsnr, shift))
		shift, xfactor, snr = apTiltShift.getTiltedRotateShift(arrayold, arraynew, difftilt, bestangle, msg=True)
		print "best tilt axis angle=", bestsnr, bestangle, shift
		self.logger.info('best tilt axis angle = %.2f (snr = %.2f; shift = %s)'%(bestangle, bestsnr, shift))

		### construct the results matrix
		radangle = math.radians(bestangle)
		raddifftilt = math.radians(difftilt)	
		### rotate by radangle, compress by raddifftilt, rotate by -radangle
		if difftilt > 0:
			result = numpy.array([
				[	math.cos(radangle)**2 + math.sin(radangle)**2*math.cos(raddifftilt),
					(1.0-math.cos(raddifftilt)) * math.cos(radangle)*math.sin(radangle), 
					0.0
				], 
				[	(1.0-math.cos(raddifftilt)) * math.cos(radangle)*math.sin(radangle), 
					math.sin(radangle)**2 + math.cos(radangle)**2*math.cos(raddifftilt),
					0.0
				], 
				[shift[0], shift[1], 1.0]], 
				dtype=numpy.float32)
		else:
			result = numpy.array([
				[	math.cos(radangle)**2 + math.sin(radangle)**2/math.cos(raddifftilt),
					(1.0-1.0/math.cos(raddifftilt)) * math.cos(radangle)*math.sin(radangle), 
					0.0
				], 
				[	(1.0-1.0/math.cos(raddifftilt)) * math.cos(radangle)*math.sin(radangle), 
					math.sin(radangle)**2 + math.cos(radangle)**2/math.cos(raddifftilt),
					0.0
				], 
				[shift[0], shift[1], 1.0]], 
				dtype=numpy.float32)
		print "result=\n", numpy.asarray(result*100, dtype=numpy.int8)

		return result

	#====================
	def alreadyAcquired(self, target, presetname):
		return False

	#====================
	def getTiltSeries(self, targetdata, presetdata):
		'''
		targetdata argument is target about to be acquired.  Find the tilt
		series that this new image will belong to if it exists, otherwise
		create a new tilt series.
		'''
		commontarget = targetdata['image']['target']
		targetnumber = targetdata['number']
		qimage1 = leginondata.AcquisitionImageData(target=commontarget)
		qtarget = leginondata.AcquisitionImageTargetData(image=qimage1, number=targetnumber)
		qpreset = leginondata.PresetData(name=presetdata['name'], session=presetdata['session'])
		qimage2 = leginondata.AcquisitionImageData(target=qtarget, preset=qpreset, session=presetdata['session'])
		images = self.research(qimage2, readimages=False)
		if images:
			tiltseries = images[0]['tilt series']
			defocus = images[0]['scope']['defocus']
		else:
			tiltseries = None
			defocus = None
		return tiltseries, defocus

	#====================
	def moveAndPreset(self, presetdata, emtarget):
		'''
		extend Acquisition.moveAndPreset because additionally we need to
		return to the same defocus as the other images in the tilt series
		'''
		status = acquisition.Acquisition.moveAndPreset(self, presetdata, emtarget)
		if status == 'error':
			return status
		targetdata = emtarget['target']
		tiltseries,defocus = self.getTiltSeries(targetdata, presetdata)
		if tiltseries is None:
			self.tiltseries = leginondata.TiltSeriesData()
			self.publish(self.tiltseries, database=True, dbforce=True)
		else:
			self.tiltseries = tiltseries
		return status

	#====================
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
		regions, image  = libCVwrapper.FindRegions(im, minsize, maxsize)

		# this is copied from targetfinder:
		#regions,image = libCVwrapper.FindRegions(self.mosaicimage, minsize, maxsize)
		n = len(regions)
		self.logger.info('Regions found: %s' % (n,))
		self.displayRegions(regions)

	#====================
	def displayRegions(self, regions):
		targets = []
		limit = 1500
		for i,region in enumerate(regions):
			if i > limit:
				break
			r,c = region['regionEllipse'][:2]
			targets.append((c,r))
		self.setTargets(targets, 'Peak')

	#====================
	def acquireImage(self):
		errstr = 'Acquire image failed: %s'
		if self.presetsclient.getCurrentPreset() is None:
			self.logger.error('Preset is unknown')
			return

		try:
			imagedata = self.acquireCorrectedCameraImageData()
		except:
			self.logger.error(errstr % 'unable to get corrected image')
			return

		if imagedata is None:
			self.logger.error('Acquire image failed')
			return

		return imagedata['image']


