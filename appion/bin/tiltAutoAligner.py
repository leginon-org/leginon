#!/usr/bin/env python

### python
import os
import sys
import time
import wx
import threading
### appion
import particleLoop2
import apFindEM
import apParam
import appionData
import apDatabase
import apDisplay
import apParticle
import apPeaks
import apImage
import ApTiltPicker
from apTilt import apTiltTransform, apTiltShift, apTiltPair
try:
	import radermacher
except:
	print "using slow tilt angle calculator"
	import slowmacher as radermacher
### numpy/scipy
import numpy
import pyami.quietscipy
from scipy import ndimage, optimize

##################################
##
##################################

class tiltAligner(particleLoop2.ParticleLoop):
	#####################################################
	##### START PRE-DEFINED PARTICLE LOOP FUNCTIONS #####
	#####################################################

	#---------------------------------------
	#---------------------------------------
	def setProcessingDirName(self):
		self.processdirname = "tiltalign"

	#---------------------------------------
	#---------------------------------------
	def preLoopFunctions(self):
		self.data = {}
		if self.params['sessionname'] is not None:
			self.processAndSaveAllImages()
		self.params['pickdatadir'] = os.path.join(self.params['rundir'],"pickdata")
		apParam.createDirectory(self.params['pickdatadir'], warning=False)

	#---------------------------------------
	#---------------------------------------
	def setupParserOptions(self):
		### Input value options
		self.outtypes = ['text','xml','spider','pickle']
		self.parser.add_option("--outtype", dest="outtype", default="spider",
			help="file output type: "+str(self.outtypes), metavar="TYPE")
		self.parser.add_option("--pickrunids", dest="pickrunids",
			help="selection run ids for previous automated picking run", metavar="#,#,#")
		self.parser.add_option("--pickrunname", dest="pickrunname", type="int",
			help="previous selection run name, e.g. --pickrunname=dogrun1", metavar="NAME")

	#---------------------------------------
	#---------------------------------------
	def checkConflicts(self):
		"""
		put in any additional conflicting parameters
		"""
		for i,v in enumerate(self.outtypes):
			if self.params['outtype'] == v:
				self.params['outtypeindex'] = i
		if self.params['outtypeindex'] is None:
			apDisplay.printError("outtype must be one of: "+str(self.outtypes)+"; NOT "+str(self.params['outtype']))
		return

	#---------------------------------------
	#---------------------------------------
	def getParticleParamsData(self):
		tiltparamsq = appionData.ApTiltAlignParamsData()
		tiltparamsq['output_type'] = self.params['outtype']
		if self.params['pickrunids'] is not None:
			self.params['pickrunidlist'] = self.params['pickrunids'].split(",")
			tiltparamsq['oldselectionrun'] = apParticle.getSelectionRunDataFromID(self.params['pickrunidlist'][0])
		return tiltparamsq

	#####################################################
	##### START PRE-DEFINED APPION LOOP FUNCTIONS #####
	#####################################################

	#---------------------------------------
	#---------------------------------------
	def loopProcessImage(self, imgdata):
		"""
		Over-writes the particleLoop processImage and uses the appionLoop processImage
		"""
		#GET THE TILT PAIR
		tiltdata = apTiltPair.getTiltPair(imgdata)
		if tiltdata is None:
			return

		if self.params['sessionname'] is None:
			apFindEM.processAndSaveImage(imgdata, params=self.params)
			apFindEM.processAndSaveImage(tiltdata, params=self.params)

		#RUN THE ALIGNER GUI
		self.runTiltAligner(imgdata, tiltdata)
		numpeaks = len(self.peaktree1)
		#apDisplay.printMsg("Found "+str(numpeaks)+" particles for "+apDisplay.shortenImageName(imgdata['filename']))
		self.stats['lastpeaks'] = numpeaks

		procimgpath = os.path.join(self.params['rundir'], imgdata['filename']+'.dwn.mrc')
		if os.path.isfile(procimgpath):
			#apDisplay.printMsg("reading processing mrc for reg")
			procimg1 = apImage.mrcToArray(procimgpath, msg=False)
		procimgpath = os.path.join(self.params['rundir'], tiltdata['filename']+'.dwn.mrc')
		if os.path.isfile(procimgpath):
			#apDisplay.printMsg("reading processing mrc for tilt")
			procimg2 = apImage.mrcToArray(procimgpath, msg=False)
		procimg1, procimg2 = apTiltTransform.maskOverlapRegion(procimg1, procimg2, self.data)

		#CREATE PEAK JPEG
		if self.threadJpeg is True:
			threading.Thread(target=apPeaks.createTiltedPeakJpeg, args=(imgdata, tiltdata, self.peaktree1,
				self.peaktree2, self.params, procimg1, procimg2)).start()
		else:
			apPeaks.createTiltedPeakJpeg(imgdata, tiltdata, self.peaktree1, self.peaktree2, self.params,
				procimg1, procimg2)

		#EXTRA DONE DICT CALL
		self._writeDoneDict(tiltdata['filename'])

	#---------------------------------------
	#---------------------------------------
	def loopCommitToDatabase(self, imgdata):
		"""
		Over-writes the particleLoop commit and uses the appionLoop commit
		"""
		tiltdata = apTiltPair.getTiltPair(imgdata)
		if tiltdata is None:
			apDisplay.printWarning("Tilt data not found; not commiting data")
			return False

		### insert the runid
		self.commitRunToDatabase(imgdata['session'], True)

		if len(self.peaktree1) < 3 or len(self.peaktree1) < 3:
			apDisplay.printWarning("Not enough particle picks; not commiting transform or particle data")
			return False

		### insert the transform
		transdata = apTiltPair.insertTiltTransform(imgdata, tiltdata, self.data, self.params)
		### insert the particles

		self.insertParticlePeakPairs(imgdata, tiltdata, transdata)
		### insert image assessment


	##########################################
	##### END PRE-DEFINED LOOP FUNCTIONS #####
	##########################################

	#---------------------------------------
	#---------------------------------------
	def insertParticlePeakPairs(self, imgdata, tiltdata, transdata):
		if transdata is not None:
			apDisplay.printMsg("insertParticlePeakPairs")
			apParticle.insertParticlePeakPairs(self.peaktree1, self.peaktree2, self.peakerrors,
				imgdata, tiltdata, transdata, self.params)
			apDisplay.printMsg("done")

	#---------------------------------------
	#---------------------------------------
	def getParticlePicks(self, imgdata):
		particles = []
		if self.params['pickrunids'] is not None:
			self.params['pickrunidlist'] = self.params['pickrunids'].split(",")
			for pickrunid in self.params['pickrunidlist']:
				newparticles = apParticle.getParticles(imgdata, pickrunid)
				particles.extend(newparticles)
		targets = self.particlesToTargets(particles)
		#apDisplay.printMsg("Found "+str(len(targets))+" particles for image "+apDisplay.short(imgdata['filename']))
		return targets

	#---------------------------------------
	#---------------------------------------
	def particlesToTargets(self, particles):
		targets = []
		for p in particles:
			targets.append( (p['xcoord']/self.params['bin'], p['ycoord']/self.params['bin']) )
		ntargets = numpy.array(targets, dtype=numpy.int32)
		return ntargets

	#---------------------------------------
	#---------------------------------------
	def parseTiltParams(self):
		theta = self.tiltparams['theta']
		gamma = self.tiltparams['gamma']
		phi   = self.tiltparams['phi']

	#---------------------------------------
	#---------------------------------------
	def processAndSaveAllImages(self):
		print "Pre-processing images before picking\nNow is a good time to go get a candy bar"
		count = 0
		total = len(self.imgtree)
		for imgdata in self.imgtree:
			count += 1
			tiltdata = apTiltPair.getTiltPair(imgdata)
			if tiltdata is None:
				#reject it
				apDatabase.insertImgAssessmentStatus(imgdata, "notiltpair", False)
				continue

			#First the image
			imgpath = os.path.join(self.params['rundir'], imgdata['filename']+'.dwn.mrc')
			if os.path.isfile(imgpath):
				sys.stderr.write(".")
				#print "already processed: ",apDisplay.short(imgdata['filename'])
			else:
				sys.stderr.write("#")
				#print "processing: ",apDisplay.short(imgdata['filename'])
				apFindEM.processAndSaveImage(imgdata, params=self.params)

			#Now for its tilt pair
			tiltpath = os.path.join(self.params['rundir'], tiltdata['filename']+'.dwn.mrc')
			if os.path.isfile(tiltpath):
				sys.stderr.write(".")
				#print "already processed: ",apDisplay.short(tiltdata['filename'])
			else:
				sys.stderr.write("#")
				#print "processing: ",apDisplay.short(tiltdata['filename'])
				apFindEM.processAndSaveImage(tiltdata, params=self.params)

			if count % 30 == 0:
				sys.stderr.write(" %d left\n" % (total-count))

	#---------------------------------------
	#---------------------------------------
	def getTiltAssess(self, imgdata, tiltdata):
		ass1 = apDatabase.getImgCompleteStatus(imgdata)
		ass2 = apDatabase.getImgCompleteStatus(tiltdata)
		if ass1 is False or ass2 is False:
			return False
		if ass1 is True and ass2 is True:
			return True
		return None

	#---------------------------------------
	#---------------------------------------
	def importPicks(self, picks1, picks2, tight=False):
		t0 = time.time()
		apDisplay.printMsg("import picks")
		#print picks1
		#print self.currentpicks1
		curpicks1 = numpy.asarray(self.currentpicks1)
		curpicks2 = numpy.asarray(self.currentpicks2)
		#print curpicks1

		# get picks
		apTiltTransform.setPointsFromArrays(curpicks1, curpicks2, self.data)
		pixdiam = self.params['diam']/self.params['apix']/self.params['bin']
		if tight is True:
			pixdiam /= 4.0
		#print self.data, pixdiam
		list1, list2 = apTiltTransform.alignPicks2(picks1, picks2, self.data, limit=pixdiam)
		if list1.shape[0] == 0 or list2.shape[0] == 0:
			apDisplay.printWarning("No new picks were found")

		# merge picks
		newpicks1, newpicks2 = apTiltTransform.betterMergePicks(curpicks1, list1, curpicks2, list2)
		newparts = newpicks1.shape[0] - curpicks1.shape[0]

		# copy over picks
		self.currentpicks1 = newpicks1
		self.currentpicks2 = newpicks2

		apDisplay.printMsg("Inserted "+str(newparts)+" new particles in "+apDisplay.timeString(time.time()-t0))

		return True

	#---------------------------------------
	#---------------------------------------
	def optimizeAngles(self):
		apDisplay.printMsg("optimize angles")
		t0 = time.time()
		if len(self.currentpicks1) < 5 or len(self.currentpicks2) < 5:
			apDisplay.printWarning("Not enough particles ot run program on image pair")
			return
		### run find theta
		na1 = numpy.array(self.currentpicks1, dtype=numpy.int32)
		na2 = numpy.array(self.currentpicks2, dtype=numpy.int32)
		fittheta = radermacher.tiltang(na1, na2, 5000.0)
		if fittheta and 'wtheta' in fittheta:
			theta = fittheta['wtheta']
			thetadev = fittheta['wthetadev']
			thetastr = ("%3.3f +/- %2.2f" % (theta, thetadev))
			tristr = apDisplay.orderOfMag(fittheta['numtri'])+" of "+apDisplay.orderOfMag(fittheta['tottri'])
			percent = str("%")
			tristr = (" (%3.1f " % (100.0 * fittheta['numtri'] / float(fittheta['tottri'])))+"%) "
			apDisplay.printMsg("Tilt angle "+thetastr+tristr)
			self.data['theta'] = fittheta['wtheta']
		### run optimize angles
		lastiter = [80,80,80]
		count = 0
		totaliter = 0
		while max(lastiter) > 75 and count < 30:
			count += 1
			lsfit = self.runLeastSquares()
			lastiter[2] = lastiter[1]
			lastiter[1] = lastiter[0]
			lastiter[0] = lsfit['iter']
			totaliter += lsfit['iter']
		apDisplay.printMsg("Least Squares: "+str(count)+" rounds, "+str(totaliter)
			+" iters, rmsd of "+str(round(lsfit['rmsd'],4))+" pixels in "+apDisplay.timeString(time.time()-t0))
		return

	#---------------------------------------
	#---------------------------------------
	def runLeastSquares(self):
		#SET XSCALE
		xscale = numpy.array((1,1,1,0,1,1), dtype=numpy.float32)
		#GET TARGETS
		a1 = self.currentpicks1
		a2 = self.currentpicks2
		if len(a1) > len(a2):
			print "shorten a1"
			a1 = a1[0:len(a2),:]
		elif len(a2) > len(a1):
			print "shorten a2"
			a2 = a2[0:len(a1),:]
		lsfit = apTiltTransform.willsq(a1, a2, self.data['theta'], self.data['gamma'],
			self.data['phi'], 1.0, self.data['shiftx'], self.data['shifty'], xscale)
		if lsfit['rmsd'] < 30:
			self.data['theta']  = lsfit['theta']
			self.data['gamma']  = lsfit['gamma']
			self.data['phi']    = lsfit['phi']
			self.data['shiftx'] = lsfit['shiftx']
			self.data['shifty']	= lsfit['shifty']
		return lsfit

	#---------------------------------------
	#---------------------------------------
	def getRmsdArray(self):
		targets1 = self.currentpicks1
		aligned1 = self.getAlignedArray2()
		if len(targets1) != len(aligned1):
			targets1 = numpy.vstack((targets1, aligned1[len(targets1):]))
			aligned1 = numpy.vstack((aligned1, targets1[len(aligned1):]))
		diffmat1 = (targets1 - aligned1)
		sqsum1 = diffmat1[:,0]**2 + diffmat1[:,1]**2
		rmsd1 = numpy.sqrt(sqsum1)
		return rmsd1

	#---------------------------------------
	#---------------------------------------
	def getAlignedArray2(self):
		apTiltTransform.setPointsFromArrays(self.currentpicks1, self.currentpicks2, self.data)
		a2b = apTiltTransform.a2Toa1Data(self.currentpicks2, self.data)
		return a2b

	#---------------------------------------
	#---------------------------------------
	def getCutoffCriteria(self, errorArray):
		#do a small minimum filter to  get rid of outliers
		size = int(len(errorArray)**0.3)+1
		errorArray2 = ndimage.minimum_filter(errorArray, size=size, mode='wrap')
		mean = ndimage.mean(errorArray2)
		stdev = ndimage.standard_deviation(errorArray2)
		cut = mean + 4.0 * stdev + 2.0
		return cut

	#---------------------------------------
	#---------------------------------------
	def clearBadPicks(self):
		apDisplay.printMsg("clear bad picks")
		a1 = self.currentpicks1
		a2 = self.currentpicks2
		origpicks = max(len(a1), len(a2))
		if len(a1) != len(a2):
			apDisplay.printMsg("uneven arrays, get rid of extra")
			#uneven arrays, get rid of extra
			self.currentpicks1 = a1[0:len(a2),:]
			self.currentpicks2 = a2[0:len(a1),:]
			return
		err = self.getRmsdArray()
		cut = self.getCutoffCriteria(err)
		a1c = []
		a2c = []
		maxerr = 4.0
		worst1 = []
		worst2 = []
		for i,e in enumerate(err):
			if i != 0 and e > maxerr:
				if len(worst1) > 0 and maxerr < cut:
					a1c.append(worst1)
					a2c.append(worst2)
				maxerr = e
				worst1 = a1[i,:]
				worst2 = a2[i,:]
			elif e < cut and (i == 0 or e > 0):
				#good picks
				a1c.append(a1[i,:])
				a2c.append(a2[i,:])
		a1d = numpy.asarray(a1c)
		a2d = numpy.asarray(a2c)
		self.currentpicks1 = a1d
		self.currentpicks2 = a2d
		newpicks = len(a1d)
		apDisplay.printMsg("removed "+str(origpicks-newpicks)+" particles")
		return

	#---------------------------------------
	#---------------------------------------
	def deleteFirstPick(self):
		a1 = self.currentpicks1
		a2 = self.currentpicks2
		a1b = a1[1:]
		a2b = a2[1:]
		self.currentpicks1 = a1b
		self.currentpicks2 = a2b

	#---------------------------------------
	#---------------------------------------
	def getOverlap(self, image1, image2):
		t0 = time.time()
		apDisplay.printMsg("get overlap")
		bestOverlap, tiltOverlap = apTiltTransform.getOverlapPercent(image1, image2, self.data)
		overlapStr = str(round(100*bestOverlap,2))+"% and "+str(round(100*tiltOverlap,2))+"%"
		apDisplay.printMsg("found overlaps of "+overlapStr+" in "+apDisplay.timeString(time.time()-t0))
		self.data['overlap'] = bestOverlap

	#---------------------------------------
	#---------------------------------------
	def runTiltAligner(self, imgdata, tiltdata):
		#set tilt
		tilt1 = apDatabase.getTiltAngleDeg(imgdata)
		tilt2 = apDatabase.getTiltAngleDeg(tiltdata)
		theta = abs(tilt2) - abs(tilt1)
		self.data['theta'] = theta
		self.data['shiftx'] = 0.0
		self.data['shifty'] = 0.0
		self.data['scale'] = 1.0

		#pre-load particle picks
		picks1 = self.getParticlePicks(imgdata)
		picks2 = self.getParticlePicks(tiltdata)
		if len(picks1) < 10 or len(picks2) < 10:
			apDisplay.printWarning("Not enough particles ot run program on image pair")
			self.badprocess = True
			return

		#open image file 1
		imgname  = imgdata['filename']+".dwn.mrc"
		imgpath  = os.path.join(self.params['rundir'], imgname)
		img1 = apImage.mrcToArray(imgpath)

		#open tilt file 2
		tiltname = tiltdata['filename']+".dwn.mrc"
		tiltpath = os.path.join(self.params['rundir'], tiltname)
		img2 = apImage.mrcToArray(tiltpath)

		#guess the shift
		t0 = time.time()
		origin, newpart, snr, bestang = apTiltShift.getTiltedCoordinates(img1, img2, theta, picks1, angsearch=True)
		self.data['gamma'] = float(bestang)
		self.data['phi'] = float(bestang)
		if snr < 2.0:
			apDisplay.printWarning("Low confidence in initial shift")
			self.badprocess = True
			return
		self.currentpicks1 = [origin]
		self.currentpicks2 = [newpart]

		self.importPicks(picks1, picks2, tight=False)
		self.deleteFirstPick()
		self.clearBadPicks()
		self.optimizeAngles()
		self.clearBadPicks()
		self.clearBadPicks()
		self.optimizeAngles()
		self.clearBadPicks()
		self.importPicks(picks1, picks2, tight=False)
		self.clearBadPicks()
		self.optimizeAngles()
		self.clearBadPicks()
		self.clearBadPicks()
		self.optimizeAngles()
		self.clearBadPicks()
		self.importPicks(picks1, picks2, tight=True)
		self.clearBadPicks()
		self.optimizeAngles()
		self.getOverlap(img1,img2)
		apDisplay.printMsg("completed alignment of "+str(len(self.currentpicks1))
			+" particle pairs in "+apDisplay.timeString(time.time()-t0))

		print self.data
		# 1. tilt data are copied to self.tiltparams by app
		# 2. particles picks are copied to self.peaks1 and self.peaks2 by app
		# 3. particle errors are copied to self.peakerrors by app
		# 4. assessment status is  copied to self.assess
		self.peaktree1 = apPeaks.convertListToPeaks(self.currentpicks1, self.params)
		self.peaktree2 = apPeaks.convertListToPeaks(self.currentpicks2, self.params)
		self.peakerrors = self.getRmsdArray()


#---------------------------------------
#---------------------------------------
#---------------------------------------
#---------------------------------------
if __name__ == '__main__':
	imgLoop = tiltAligner()
	imgLoop.run()



