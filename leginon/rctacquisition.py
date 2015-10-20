#
# COPYRIGHT:
#	   The Leginon software is Copyright 2003
#	   The Scripps Research Institute, La Jolla, CA
#	   For terms of the license agreement
#	   see  http://ami.scripps.edu/software/leginon-license
#
from leginon import leginondata
import acquisition
import gui.wx.RCTAcquisition
try:
	import openCVcaller
	NO_CV = False
except:
	NO_CV = True
import pyami.timedproc
import numpy
import time
import math
import pyami.quietscipy
import pyami.mrc as mrc
from scipy import ndimage
from leginon import transformregistration
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
		'tilts': '(-45, 0)',
		'stepsize': 42.0,
		'pause': 1.0,
		'lowfilt': 1,
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
		self.tilttest_cycle = 0
		self.shiftmatrix_maker = transformregistration.CorrelationRegistration(self)
		self.showCVImportError()

	def showCVImportError(self):
		if NO_CV:
			self.logger.error('Computer vision module import error. Can not run RCT')
	#====================
	def setImageFilename(self, imagedata):
		setImageFilename(imagedata, tiltnumber=self.tiltnumber)
		imagedata['tilt series'] = self.tiltseries

	#====================
	def processTargetList(self, tilt0targetlist):
		'''
		We override this so we can process each target list for each tilt
		'''
		# reset tilt test cycle
		self.tilttest_cycle = 0

		## return if no targets in list
		tilt0targets = self.researchTargets(list=tilt0targetlist, status='new')
		if not tilt0targets:
			self.reportTargetListDone(tilt0targetlist, 'success')
			return

		tilts = self.convertDegreeTiltsToRadianList(self.settings['tilts'])

		## parent image and tilt of parent image
		image0 = tilt0targetlist['image']
		tilt0 = image0['scope']['stage position']['a']
		self.logger.info('image0 tilt = %s degrees' % (degrees(tilt0),))

		## loop through each tilt
		for i,tilt in enumerate(tilts):
			if self.player.state() == 'stop':
				break
			self.tiltnumber = i

			## only make new targets if tilt is different than tilt0
			tiltedtargetlist = self.tiltTargets(tilt0, tilt, tilt0targetlist)
			if tiltedtargetlist is None:
				self.reportTargetListDone(tilt0targetlist, 'failure')
				return

			self.logger.info('doing tilt %d = %s degrees' % (i+1, degrees(tilt),))
			self.instrument.tem.StagePosition = {'a': tilt}

			## drift check
			#self.declareDrift('rct')
			# drift is checked only if threshold is bigger than zero
			# drift threshold is in meters/sec
			if self.settings['drift threshold'] > 1e-8:
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

			#self.declaredrifteachtarget = True
			self.setTargets([], 'Peak')
			acquisition.Acquisition.processTargetList(self, tiltedtargetlist)
			#self.declaredrifteachtarget = False

		self.logger.info('returning to tilt0')
		self.instrument.tem.StagePosition = {'a': tilt0}
		self.reportTargetListDone(tilt0targetlist, 'success')

	def avoidTargetAdjustment(self,target_to_adjust,recent_target):
		'''
		RCT should not adjust targets.  StageTracking is doing it.
		The way imagehandler getLastParentImage looks for last version
		give wrong results since tilt number is not part of the query
		and stage tracked image version is reset to 0.
		The drift after stage tilt and focus will not be adjusted this way.
		However, since the targets are moved by iterative navigator move,
		this should be o.k.
		'''
		return True

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
		self.logger.info('Running tiltTargets')
		# find matrix
		image0 = tilt0targetlist['image']
		tilt0targets = self.researchTargets(list=tilt0targetlist, status='new')
		matrix,tiltedimagedata = self.trackStage(image0, tilt0, tilt, tilt0targets)
		if matrix is None:
			return None

		# transformTargets for display purposes only
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

	def isSmallTiltDifference(self,tilts,i,tilt0):
		'''
		Determine if phase correlation should be used for matching
		'''
		newtilt = tilts[i]
		if i == 0:
			oldtilt = tilt0
		else:
			oldtilt = tilts[i-1]
		# high tilt is more sensitive to distortion
		# At 0.2 radians, the largest target position distortion is 2% at the edge of the image.
		if abs(newtilt - oldtilt) < 0.2 and (abs(oldtilt) < 0.2 or abs(newtilt) < 0.2):
			return True
		return False

	def affineToText(self, affineresult):
		return openCVcaller.affineToText(affineresult)

	def checkArrayMinMax(self,arrayold, arraynew):
		openCVcaller.checkArrayMinMax(self, arrayold, arraynew)

	def runMatchImages(self, arrayold, arraynew):
		#timeout = 300
		minsize = self.settings['minsize']
		maxsize = self.settings['maxsize']
		#result = pyami.timedproc.call('leginon.openCVcaller', 'MatchImages', args=(arrayold, arraynew, minsize, maxsize), timeout=timeout)
		result = openCVcaller.MatchImages(arrayold, arraynew)
		self.logger.info("result matrix= "+str(numpy.asarray(result*100, dtype=numpy.int8).ravel()))
		return result
					
	def runFindRegions(self, im):
		minsize = self.settings['minsize']
		maxsize = self.settings['maxsize']
		#timeout = 300
		#features, image  = openCVcaller.FindRegions(im, minsize, maxsize)
		#self.logger.info('running libCV.FindRegions, timeout = %d' % (timeout,))
		#features,image = pyami.timedproc.call('leginon.openCVcaller', 'FindRegions', args=(im,minsize,maxsize), timeout=timeout)
		features  = openCVcaller.FindFeatures(im)
		return features

	def checkCVResult(self,result, is_small_tilt_diff=False):
		return openCVcaller.checkOpenCVResult(self.logger, result, is_small_tilt_diff)

	def modifyImage(self, array, thresh=0, do_phase_correlation=False):
		if do_phase_correlation:
			medfilt=0
			blur=0
		else:
			medfilt = int(self.settings['medfilt'])
			blur = int(self.settings['lowfilt'])
			if blur % 2 == 0:
				self.logger.warning('openCV blur function takes only odd number')
				blur += 1
				self.logger.warning('advance lowfilt used to %d' % blur)
		if medfilt > 1:
			array = ndimage.median_filter(array, size=medfilt)
		return openCVcaller.modifyImage(array,blur,thresh)

	#====================
	def trackStage(self, image0, tilt0, tilt, tilt0targets):
		self.logger.info('Running trackStage')
		retriesmax = 15
		retries = retriesmax
		thresh = 0
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
		imageold = image0
		#imageold = leginondata.AcquisitionImageData(initializer=imageold)
		#imageold['image']=mrc.read('/Users/acheng/tests/test_libcv/arrayold.mrc')
		arrayold = numpy.asarray(imageold['image'], dtype=numpy.float32)
		self.setImage(arrayold, 'Image')
		runningresult = numpy.identity(3, numpy.float32)

		# transformTargets for display purposes only
		self.transformTargets(runningresult, tilt0targets)

		#for tilt in tilts:
		### use while loop so we can backtrack
		i = 0
		while i < len(tilts)-1:
			i+=1
			tilt = float("%.3f"%tilts[i])
			self.logger.info('Going to tilt angle: %.2f' % (degrees(tilt),))
			self.instrument.tem.StagePosition = {'a': tilt}
			is_small_tilt_diff = self.isSmallTiltDifference(tilts,i,tilt0)
			if pausetime > 0.1:
				self.logger.info('Pausing %.1f seconds' %(pausetime,))
				time.sleep(pausetime)
			self.logger.info('Acquire intermediate tilted parent image')
			imagenew = self.acquireCorrectedCameraImageData()
			# Testing
			#imagenew = leginondata.AcquisitionImageData(initializer=imagenew)
			#imagenew['image']=mrc.read('/Users/acheng/tests/test_libcv/arraynew.mrc')
			arraynew = imagenew['image']

			# modifyImage here so that thresh is set within while loop
			print "THRESH = ", thresh						 
			arrayold = self.modifyImage(arrayold, thresh, is_small_tilt_diff)
			arraynew = self.modifyImage(arraynew,thresh,is_small_tilt_diff)

			self.setImage(arraynew, 'Image')

			if is_small_tilt_diff:
				self.logger.info('Use phase correlation on small tilt')
				result = numpy.array(self.shiftmatrix_maker.register(arrayold, arraynew))
			else:

				print '============ CV stuff ============'

				self.logger.info('CV stuff')
				self.checkArrayMinMax(arrayold, arraynew)

				print 'tilt', tilts[i]*180/3.14159

				try:
					result = self.runMatchImages(arrayold,arraynew)
				except:
					raise
					self.logger.error('CV library MatchImages failed')
					return None,None
					
				check = self.checkCVResult(result, is_small_tilt_diff)
				if check is False:
					self.logger.warning("CV transform failed: redoing tilt %.2f"%(tilt,))
					### redo this tilt; becomes an infinite loop if the image goes black
					self.logger.warning("openCV failed: redoing tilt %.2f"%(tilt,))
					if retries:
						i -= 1
						retries -= 1
						if retries <= retriesmax/2:
							# Use a different threshold to perturb the images
							thresh = 1
							print "THRESH = 1"						 
						print "retries =", retries, "out of", retriesmax
					else:
						print "Tilt openCV FAILED"
						self.logger.error("openCV failed: giving up")
						self.instrument.tem.StagePosition = {'a': tilt0}
						return None, None
					continue
				else:
					retries = 0		 
				print '============ CV match images done ============'

			self.logger.info("result matrix= "+str(numpy.asarray(result*100, dtype=numpy.int8).ravel()))
			self.logger.info( "Inter Matrix: "+self.affineToText(result) )

			runningresult = numpy.dot(runningresult, result)
			# transformTargets for display purposes only
			self.transformTargets(runningresult, tilt0targets)
			self.logger.info( "Running Matrix: "+self.affineToText(runningresult) )
			self.logger.info("running result matrix= "+str(numpy.asarray(runningresult*100, dtype=numpy.int8).ravel()))
			# libcv usage end
			imageold = imagenew
			# get from imagedata so that it is not modified
			arrayold = numpy.asarray(imageold['image'], dtype=numpy.float32)

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

		self.logger.info( "FINAL Matrix: "+self.affineToText(runningresult) )
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
		### These are commented out in Peter Kraft's version
		'''
		if maxangle < 20 or diffangle < 10:
			# no intermediate step required
			nsteps = 0
		else:
			# always have at least one intermediate step
			nsteps = 1
		'''
		nsteps = 0
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
		if nsteps > 5 and self.settings['stepsize'] < bigstepsize:
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
		im = self.modifyImage(im,0,False)
		self.setImage(im)

		try:
			features = self.runFindRegions(im)
		except:
			self.logger.error('CV Find Features failed')
			features = []

		n = len(features)
		self.logger.info('Regions found: %s' % (n,))
		self.displayRegions(features)

	#====================
	def displayRegions(self, features):
		targets = []
		limit = 1500
		for i,feature in enumerate(features):
			if i > limit:
				break
			x, y = feature
			targets.append((x,y))
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

	def testTilt(self):
		origstage = self.instrument.tem.StagePosition
		orig_tilt = origstage['a']
		tilts = self.convertDegreeTiltsToRadianList(self.settings['tilts'])
		if len(tilts) == 0:
			self.logger.error('Need to set tilts in settings to test tilts')
		if self.tilttest_cycle >= len(tilts):
			self.tilttest_cycle = 0
		this_tilt = tilts[self.tilttest_cycle]
		this_tilt_degrees = degrees(this_tilt)
		self.instrument.tem.StagePosition = {'a': this_tilt}
		self.logger.info('Stage Tilted to %.1f degrees' % this_tilt_degrees)
		self.tilttest_cycle += 1
		im = self.testAcquire()
		if orig_tilt != this_tilt:
			self.instrument.tem.StagePosition = {'a': orig_tilt}
			self.logger.info('Tilt Stage back to %.1f degrees' % degrees(orig_tilt))
